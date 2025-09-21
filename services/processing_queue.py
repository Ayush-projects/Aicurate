"""
Processing Queue Service with retry mechanism for AI processing
"""

import asyncio
import logging
import threading
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import queue
from services.firebase_service import firebase_service
from services.ai_agent import ai_agent
from firebase_admin import firestore

logger = logging.getLogger(__name__)

class ProcessingStatus(Enum):
    PENDING = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"

@dataclass
class ProcessingJob:
    submission_id: str
    submission_data: Dict[str, Any]
    status: ProcessingStatus
    created_at: datetime
    updated_at: datetime
    retry_count: int = 0
    max_retries: int = 3
    last_error: Optional[str] = None
    next_retry_at: Optional[datetime] = None

class ProcessingQueue:
    def __init__(self):
        self.job_queue = queue.Queue()
        self.processing_jobs: Dict[str, ProcessingJob] = {}
        self.worker_threads = []
        self.is_running = False
        self.max_workers = 2
        self.retry_delays = [60, 300, 900]  # 1 min, 5 min, 15 min
        
    def start(self):
        """Start the processing queue workers"""
        if self.is_running:
            return
            
        self.is_running = True
        logger.info("Starting processing queue workers...")
        
        # Start worker threads
        for i in range(self.max_workers):
            worker = threading.Thread(target=self._worker_loop, daemon=True, name=f"ProcessingWorker-{i}")
            worker.start()
            self.worker_threads.append(worker)
        
        # Start retry checker
        retry_thread = threading.Thread(target=self._retry_loop, daemon=True, name="RetryChecker")
        retry_thread.start()
        self.worker_threads.append(retry_thread)
        
        logger.info(f"Processing queue started with {self.max_workers} workers")
    
    def stop(self):
        """Stop the processing queue"""
        self.is_running = False
        logger.info("Processing queue stopped")
    
    def queue_submission(self, submission_id: str, submission_data: Dict[str, Any]) -> bool:
        """
        Queue a submission for processing
        """
        try:
            # Check if already queued or processing
            if submission_id in self.processing_jobs:
                existing_job = self.processing_jobs[submission_id]
                if existing_job.status in [ProcessingStatus.PENDING, ProcessingStatus.PROCESSING, ProcessingStatus.RETRYING]:
                    logger.warning(f"Submission {submission_id} is already queued or processing")
                    return False
            
            # Create new job
            job = ProcessingJob(
                submission_id=submission_id,
                submission_data=submission_data,
                status=ProcessingStatus.PENDING,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            
            # Add to queue and tracking
            self.job_queue.put(job)
            self.processing_jobs[submission_id] = job
            
            # Update Firebase status
            self._update_firebase_status(submission_id, ProcessingStatus.PENDING.value)
            
            logger.info(f"Queued submission {submission_id} for processing")
            return True
            
        except Exception as e:
            logger.error(f"Error queueing submission {submission_id}: {e}")
            return False
    
    def _worker_loop(self):
        """Main worker loop for processing jobs"""
        while self.is_running:
            try:
                # Get job from queue (with timeout)
                job = self.job_queue.get(timeout=1)
                
                # Process the job
                self._process_job(job)
                
                # Mark task as done
                self.job_queue.task_done()
                
            except queue.Empty:
                # No jobs available, continue
                continue
            except Exception as e:
                logger.error(f"Error in worker loop: {e}")
                time.sleep(1)
    
    def _retry_loop(self):
        """Loop to check for jobs that need retrying"""
        while self.is_running:
            try:
                current_time = datetime.now(timezone.utc)
                
                # Check for jobs that need retrying
                for job in self.processing_jobs.values():
                    if (job.status == ProcessingStatus.RETRYING and 
                        job.next_retry_at and 
                        current_time >= job.next_retry_at):
                        
                        # Reset status and requeue
                        job.status = ProcessingStatus.PENDING
                        job.updated_at = current_time
                        job.next_retry_at = None
                        
                        self.job_queue.put(job)
                        self._update_firebase_status(job.submission_id, ProcessingStatus.PENDING.value)
                        
                        logger.info(f"Requeued submission {job.submission_id} for retry {job.retry_count + 1}")
                
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in retry loop: {e}")
                time.sleep(30)
    
    def _process_job(self, job: ProcessingJob):
        """Process a single job"""
        try:
            logger.info(f"Processing submission {job.submission_id}")
            
            # Update status to processing
            job.status = ProcessingStatus.PROCESSING
            job.updated_at = datetime.now(timezone.utc)
            self._update_firebase_status(job.submission_id, ProcessingStatus.PROCESSING.value)

            # Always fetch the freshest submission data so uploaded files are available
            submission_payload = job.submission_data or {}
            if firebase_service.db:
                try:
                    submission_ref = firebase_service.db.collection('startup_submissions').document(job.submission_id)
                    submission_doc = submission_ref.get()
                    if submission_doc.exists:
                        submission_payload = submission_doc.to_dict() or {}
                        submission_payload.setdefault('id', job.submission_id)
                        job.submission_data = submission_payload
                except Exception as fetch_error:
                    logger.warning(f"Unable to refresh submission {job.submission_id} before processing: {fetch_error}")

            # Process with AI agent
            ai_report = ai_agent.process_submission(job.submission_id, submission_payload)
            
            # Mark as completed
            job.status = ProcessingStatus.COMPLETED
            job.updated_at = datetime.now(timezone.utc)
            self._update_firebase_status(job.submission_id, ProcessingStatus.COMPLETED.value)
            
            logger.info(f"Successfully processed submission {job.submission_id}")
            
        except Exception as e:
            logger.error(f"Error processing submission {job.submission_id}: {e}")
            self._handle_processing_error(job, str(e))
    
    def _handle_processing_error(self, job: ProcessingJob, error: str):
        """Handle processing errors with retry logic"""
        job.retry_count += 1
        job.last_error = error
        job.updated_at = datetime.now(timezone.utc)
        
        if job.retry_count <= job.max_retries:
            # Calculate retry delay
            delay_seconds = self.retry_delays[min(job.retry_count - 1, len(self.retry_delays) - 1)]
            job.next_retry_at = datetime.now(timezone.utc).replace(microsecond=0) + timedelta(seconds=delay_seconds)
            
            job.status = ProcessingStatus.RETRYING
            self._update_firebase_status(job.submission_id, ProcessingStatus.RETRYING.value)
            
            logger.warning(f"Submission {job.submission_id} failed (attempt {job.retry_count}/{job.max_retries + 1}). "
                         f"Retrying in {delay_seconds} seconds. Error: {error}")
        else:
            # Max retries exceeded
            job.status = ProcessingStatus.FAILED
            self._update_firebase_status(job.submission_id, ProcessingStatus.FAILED.value)
            
            logger.error(f"Submission {job.submission_id} failed after {job.max_retries} retries. "
                        f"Final error: {error}")
    
    def _update_firebase_status(self, submission_id: str, status: str):
        """Update submission status in Firebase"""
        if not firebase_service.db:
            return

        try:
            submission_ref = firebase_service.db.collection('startup_submissions').document(submission_id)
            stage_map = {
                ProcessingStatus.PENDING.value: 'queued_for_processing',
                ProcessingStatus.PROCESSING.value: 'ai_processing',
                ProcessingStatus.COMPLETED.value: 'analysis_complete',
                ProcessingStatus.FAILED.value: 'processing_failed',
                ProcessingStatus.RETRYING.value: 'retry_wait'
            }
            submission_ref.update({
                'status': status,
                'processingStage': stage_map.get(status, status),
                'updated_at': firestore.SERVER_TIMESTAMP
            })
        except Exception as e:
            logger.error(f"Error updating Firebase status for {submission_id}: {e}")
    
    def get_job_status(self, submission_id: str) -> Optional[ProcessingJob]:
        """Get the status of a specific job"""
        return self.processing_jobs.get(submission_id)
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        stats = {
            'total_jobs': len(self.processing_jobs),
            'queued': 0,
            'processing': 0,
            'completed': 0,
            'failed': 0,
            'retrying': 0,
            'queue_size': self.job_queue.qsize()
        }
        
        for job in self.processing_jobs.values():
            stats[job.status.value] += 1
        
        return stats
    
    def cancel_job(self, submission_id: str) -> bool:
        """Cancel a job (if not already processing)"""
        if submission_id not in self.processing_jobs:
            return False
        
        job = self.processing_jobs[submission_id]
        if job.status in [ProcessingStatus.PENDING, ProcessingStatus.RETRYING]:
            job.status = ProcessingStatus.FAILED
            job.updated_at = datetime.now(timezone.utc)
            self._update_firebase_status(submission_id, ProcessingStatus.FAILED.value)
            
            # Remove from queue if possible
            try:
                # This is a simplified approach - in production you'd need a more sophisticated queue
                logger.info(f"Cancelled job {submission_id}")
                return True
            except:
                return False
        
        return False

# Global processing queue instance
processing_queue = ProcessingQueue()

# Start the queue when module is imported
processing_queue.start()
