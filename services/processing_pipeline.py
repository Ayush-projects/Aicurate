"""
Processing Pipeline Service for handling startup submissions
"""

import logging
from typing import Dict, Any
from services.processing_queue import processing_queue
from services.ai_agent import ai_agent

logger = logging.getLogger(__name__)

class ProcessingPipeline:
    def __init__(self):
        self.queue = processing_queue
    
    def queue_submission(self, submission_id: str, submission_data: Dict[str, Any]) -> bool:
        """
        Queue a submission for processing
        """
        try:
            logger.info(f"Queueing submission {submission_id} for processing")
            return self.queue.queue_submission(submission_id, submission_data)
            
        except Exception as e:
            logger.error(f"Error queueing submission {submission_id}: {e}")
            return False
    
    def get_submission_status(self, submission_id: str) -> Dict[str, Any]:
        """
        Get the processing status of a submission
        """
        try:
            job = self.queue.get_job_status(submission_id)
            if job:
                return {
                    'status': job.status.value,
                    'retry_count': job.retry_count,
                    'max_retries': job.max_retries,
                    'last_error': job.last_error,
                    'created_at': job.created_at.isoformat(),
                    'updated_at': job.updated_at.isoformat(),
                    'next_retry_at': job.next_retry_at.isoformat() if job.next_retry_at else None
                }
            else:
                return {'status': 'not_found'}
                
        except Exception as e:
            logger.error(f"Error getting submission status for {submission_id}: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """
        Get processing queue statistics
        """
        try:
            return self.queue.get_queue_stats()
        except Exception as e:
            logger.error(f"Error getting queue stats: {e}")
            return {'error': str(e)}
    
    def cancel_submission(self, submission_id: str) -> bool:
        """
        Cancel a submission processing
        """
        try:
            return self.queue.cancel_job(submission_id)
        except Exception as e:
            logger.error(f"Error cancelling submission {submission_id}: {e}")
            return False

# Global processing pipeline instance
processing_pipeline = ProcessingPipeline()