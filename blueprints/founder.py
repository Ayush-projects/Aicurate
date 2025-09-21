"""
Founder blueprint for AI Investment Platform
Handles all founder-specific routes and functionality
"""

from datetime import datetime, timezone
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from utils.auth import login_required, founder_required, get_current_user
from utils.api import APIResponse, handle_api_exception
from utils.validation import validate_required_fields, InputValidator
from services.firebase_service import firebase_service
from services.file_upload_service import file_upload_service
from services.processing_pipeline import processing_pipeline
from firebase_admin import firestore
import logging
import uuid

logger = logging.getLogger(__name__)

founder_bp = Blueprint('founder', __name__)


def _format_timestamp(value):
    """Return formatted timestamp string for template use."""
    if isinstance(value, datetime):
        return value.strftime('%Y-%m-%d %H:%M')
    return None


def _sort_timestamp(primary, fallback):
    """Return comparable datetime for sorting recent activity."""
    candidate = primary if isinstance(primary, datetime) else fallback if isinstance(fallback, datetime) else None
    if candidate:
        return candidate
    return datetime.fromtimestamp(0, tz=timezone.utc)


@founder_bp.route('/dashboard')
@login_required
@founder_required
def dashboard():
    """Founder dashboard"""
    try:
        user = get_current_user()
        if not user:
            flash('User data not found', 'error')
            return redirect(url_for('auth.login'))
        
        firestore_available = firebase_service.is_firestore_available()

        # Get founder's startups from Firestore
        startups = []
        if firestore_available:
            try:
                startups_ref = firebase_service.db.collection('startups').where('founder_id', '==', user['id'])
                startups_docs = startups_ref.stream()
                for doc in startups_docs:
                    data = doc.to_dict()
                    data['id'] = doc.id
                    data['created_at_display'] = _format_timestamp(data.get('created_at'))
                    data['updated_at_display'] = _format_timestamp(data.get('updated_at'))
                    startups.append(data)
            except Exception as e:
                logger.error(f"Error fetching startups: {e}")
                flash('Error loading startup data', 'error')

        # Get startup submissions data for stats
        submissions = []
        if firestore_available:
            try:
                submissions_ref = firebase_service.db.collection('startup_submissions').where('founder_id', '==', user['id'])
                submissions_docs = submissions_ref.stream()
                for doc in submissions_docs:
                    data = doc.to_dict()
                    data['id'] = doc.id
                    submissions.append(data)
            except Exception as e:
                logger.error(f"Error fetching submissions: {e}")

        # Calculate stats from submissions
        total_submissions = len(submissions)
        completed_submissions = sum(1 for s in submissions if s.get('status') == 'completed')
        processing_submissions = sum(1 for s in submissions if s.get('status') in ['processing', 'queued'])
        failed_submissions = sum(1 for s in submissions if s.get('status') == 'failed')
        awaiting_uploads = sum(1 for s in submissions if s.get('status') == 'awaiting_uploads')
        
        # Calculate total funding goal from submissions (if available)
        total_funding_goal = 0
        for submission in submissions:
            if 'financials' in submission and 'fundingRequiredINR' in submission['financials']:
                total_funding_goal += float(submission['financials']['fundingRequiredINR'] or 0)

        stats = {
            'total_startups': total_submissions,
            'active_startups': completed_submissions,
            'paused_startups': processing_submissions,
            'failed_startups': failed_submissions,
            'total_funding_goal': total_funding_goal,
            'awaiting_uploads': awaiting_uploads
        }

        return render_template(
            'founder/dashboard.html',
            user=user,
            stats=stats,
            startups=startups,
            submissions=submissions,
            firestore_enabled=firestore_available
        )
    
    except Exception as e:
        logger.exception(f"Error in founder dashboard: {e}")
        flash('An error occurred while loading the dashboard', 'error')
        return redirect(url_for('home'))


@founder_bp.route('/profile')
@login_required
@founder_required
def profile():
    """Founder profile page"""
    try:
        user = get_current_user()
        if not user:
            flash('User data not found', 'error')
            return redirect(url_for('auth.login'))
        
        firestore_available = firebase_service.is_firestore_available()

        return render_template(
            'founder/profile.html',
            user=user,
            firestore_enabled=firestore_available
        )
    
    except Exception as e:
        logger.exception(f"Error in founder profile: {e}")
        flash('An error occurred while loading the profile', 'error')
        return redirect(url_for('founder.dashboard'))


@founder_bp.route('/startups')
@login_required
@founder_required
def startups():
    """Founder's startups management page"""
    try:
        user = get_current_user()
        if not user:
            flash('User data not found', 'error')
            return redirect(url_for('auth.login'))
        
        firestore_available = firebase_service.is_firestore_available()

        # Get founder's startups
        startups = []
        if firestore_available:
            try:
                startups_ref = firebase_service.db.collection('startups').where('founder_id', '==', user['id'])
                startups_docs = startups_ref.stream()
                for doc in startups_docs:
                    data = {'id': doc.id, **doc.to_dict()}
                    data['created_at_display'] = _format_timestamp(data.get('created_at'))
                    data['updated_at_display'] = _format_timestamp(data.get('updated_at'))
                    startups.append(data)
            except Exception as e:
                logger.error(f"Error fetching startups: {e}")
                flash('Error loading startups', 'error')

        return render_template(
            'founder/startups.html',
            user=user,
            startups=startups,
            firestore_enabled=firestore_available
        )
    
    except Exception as e:
        logger.exception(f"Error in founder startups: {e}")
        flash('An error occurred while loading startups', 'error')
        return redirect(url_for('founder.dashboard'))


@founder_bp.route('/faq')
@login_required
@founder_required
def faq():
    """Founder FAQ page"""
    try:
        user = get_current_user()
        if not user:
            flash('User data not found', 'error')
            return redirect(url_for('auth.login'))
        
        return render_template(
            'founder/faq.html',
            user=user
        )
    
    except Exception as e:
        logger.exception(f"Error in founder FAQ: {e}")
        flash('An error occurred while loading FAQ', 'error')
        return redirect(url_for('founder.dashboard'))




@founder_bp.route('/api/startup', methods=['POST'])
@login_required
@founder_required
@handle_api_exception
def create_startup():
    """Create new startup"""
    try:
        data = request.get_json()
        user = get_current_user()
        
        if not user:
            return APIResponse.unauthorized('User not found')
        
        # Validate required fields
        required_fields = ['name', 'description', 'industry', 'funding_goal']
        validation_errors = validate_required_fields(data, required_fields)
        
        if validation_errors:
            return APIResponse.validation_error(validation_errors)
        
        # Validate specific fields
        if not InputValidator.validate_company_name(data['name']):
            validation_errors['name'] = 'Invalid company name format'
        
        if not InputValidator.validate_string_length(data['description'], min_length=10, max_length=1000):
            validation_errors['description'] = 'Description must be 10-1000 characters'
        
        if not InputValidator.validate_funding_amount(data['funding_goal']):
            validation_errors['funding_goal'] = 'Invalid funding amount'
        
        if validation_errors:
            return APIResponse.validation_error(validation_errors)
        
        # Create startup data
        startup_data = {
            'name': InputValidator.sanitize_input(data['name']),
            'description': InputValidator.sanitize_input(data['description']),
            'industry': InputValidator.sanitize_input(data['industry']),
            'funding_goal': float(data['funding_goal']),
            'founder_id': user['id'],
            'founder_email': user['email'],
            'status': 'active',
            'created_at': firestore.SERVER_TIMESTAMP if firebase_service.db else None,
            'updated_at': firestore.SERVER_TIMESTAMP if firebase_service.db else None
        }
        
        # Save to Firestore
        if firebase_service.db:
            doc_ref = firebase_service.db.collection('startups').add(startup_data)
            startup_data['id'] = doc_ref[1].id
        
        logger.info(f"Startup created: {startup_data['name']} by {user['email']}")
        return APIResponse.success(
            data=startup_data,
            message='Startup created successfully'
        )
    
    except Exception as e:
        logger.exception(f"Error creating startup: {e}")
        return APIResponse.server_error('Failed to create startup')


@founder_bp.route('/api/startup/<startup_id>', methods=['PUT'])
@login_required
@founder_required
@handle_api_exception
def update_startup(startup_id):
    """Update startup"""
    try:
        data = request.get_json()
        user = get_current_user()
        
        if not user:
            return APIResponse.unauthorized('User not found')
        
        if not firebase_service.db:
            return APIResponse.server_error('Database not available')
        
        # Check if startup exists and belongs to user
        startup_ref = firebase_service.db.collection('startups').document(startup_id)
        startup_doc = startup_ref.get()
        
        if not startup_doc.exists:
            return APIResponse.not_found('Startup not found')
        
        startup_data = startup_doc.to_dict()
        if startup_data['founder_id'] != user['id']:
            return APIResponse.forbidden('You can only update your own startups')
        
        # Validate and sanitize update data
        update_data = {}
        for field in ['name', 'description', 'industry', 'funding_goal', 'status']:
            if field in data:
                if field == 'funding_goal':
                    if not InputValidator.validate_funding_amount(data[field]):
                        return APIResponse.validation_error({field: 'Invalid funding amount'})
                    update_data[field] = float(data[field])
                elif field == 'name':
                    if not InputValidator.validate_company_name(data[field]):
                        return APIResponse.validation_error({field: 'Invalid company name format'})
                    update_data[field] = InputValidator.sanitize_input(data[field])
                elif field == 'description':
                    if not InputValidator.validate_string_length(data[field], min_length=10, max_length=1000):
                        return APIResponse.validation_error({field: 'Description must be 10-1000 characters'})
                    update_data[field] = InputValidator.sanitize_input(data[field])
                else:
                    update_data[field] = InputValidator.sanitize_input(data[field])
        
        update_data['updated_at'] = firestore.SERVER_TIMESTAMP
        
        # Update startup
        startup_ref.update(update_data)
        
        logger.info(f"Startup updated: {startup_id} by {user['email']}")
        return APIResponse.success(message='Startup updated successfully')
    
    except Exception as e:
        logger.exception(f"Error updating startup: {e}")
        return APIResponse.server_error('Failed to update startup')


@founder_bp.route('/api/startup/<startup_id>', methods=['DELETE'])
@login_required
@founder_required
@handle_api_exception
def delete_startup(startup_id):
    """Delete startup"""
    try:
        user = get_current_user()
        
        if not user:
            return APIResponse.unauthorized('User not found')
        
        if not firebase_service.db:
            return APIResponse.server_error('Database not available')
        
        # Check if startup exists and belongs to user
        startup_ref = firebase_service.db.collection('startups').document(startup_id)
        startup_doc = startup_ref.get()
        
        if not startup_doc.exists:
            return APIResponse.not_found('Startup not found')
        
        startup_data = startup_doc.to_dict()
        if startup_data['founder_id'] != user['id']:
            return APIResponse.forbidden('You can only delete your own startups')
        
        # Delete associated files
        if 'uploadedAssets' in startup_data:
            for asset in startup_data['uploadedAssets']:
                if 'file_path' in asset:
                    file_upload_service.delete_file(asset['file_path'])
        
        # Delete startup
        startup_ref.delete()
        
        logger.info(f"Startup deleted: {startup_id} by {user['email']}")
        return APIResponse.success(message='Startup deleted successfully')
    
    except Exception as e:
        logger.exception(f"Error deleting startup: {e}")
        return APIResponse.server_error('Failed to delete startup')


# New startup submission endpoints
@founder_bp.route('/api/startup-submission', methods=['POST'])
@login_required
@founder_required
@handle_api_exception
def create_startup_submission():
    """Create new startup submission with comprehensive data"""
    try:
        data = request.get_json()
        user = get_current_user()
        
        if not user:
            return APIResponse.unauthorized('User not found')
        
        # Validate submission data
        validation_errors = InputValidator.validate_startup_submission(data)
        if validation_errors:
            return APIResponse.validation_error(validation_errors)
        
        # Generate unique startup ID
        startup_id = f"strp_{uuid.uuid4().hex[:8]}"
        
        # Create submission data structure matching the JSON format
        submission_data = {
            'startupId': startup_id,
            'submission': {
                'submittedBy': user['email'],
                'submittedAt': datetime.now(timezone.utc).isoformat(),
                'startupName': InputValidator.sanitize_input(data['startupName']),
                'description': InputValidator.sanitize_input(data['description']),
                'location': {
                    'city': InputValidator.sanitize_input(data['location']['city']),
                    'state': InputValidator.sanitize_input(data['location']['state']),
                    'country': InputValidator.sanitize_input(data['location']['country'])
                },
                'foundingDate': data['foundingDate'],
                'founderIds': [user['id']],
                'uploadedAssets': []
            },
            'companyProfile': {
                'description': InputValidator.sanitize_input(data['description']),
                'tagline': InputValidator.sanitize_input(data.get('tagline', '')),
                'sector': InputValidator.sanitize_input(data.get('sector', '')),
                'subsectors': data.get('subsectors', []),
                'businessModel': InputValidator.sanitize_input(data.get('businessModel', '')),
                'companyStage': InputValidator.sanitize_input(data.get('companyStage', 'Seed')),
                'teamSize': data.get('teamSize', 1),
                'legalEntity': InputValidator.sanitize_input(data.get('legalEntity', '')),
                'corporateStructure': InputValidator.sanitize_input(data.get('corporateStructure', '')),
                'ipAssets': data.get('ipAssets', [])
            },
            'founderProfiles': [{
                'id': user['id'],
                'name': user.get('displayName') or f"{user.get('firstName', '')} {user.get('lastName', '')}".strip() or user['email'].split('@')[0],
                'linkedIn': user.get('linkedIn', ''),
                'email': user['email'],
                'education': user.get('education', ''),
                'experience': user.get('experience', []),
                'commitmentLevel': {
                    'fullTime': data.get('fullTime', True),
                    'equityHoldingPercent': data.get('equityHoldingPercent', 100),
                    'personalCapitalInvestedINR': data.get('personalCapitalInvestedINR', 0)
                },
                'founderMarketFitScore': data.get('founderMarketFitScore', 0)
            }],
            'status': 'awaiting_uploads',
            'processingStage': 'awaiting_assets',
            'created_at': firestore.SERVER_TIMESTAMP if firebase_service.db else None,
            'updated_at': firestore.SERVER_TIMESTAMP if firebase_service.db else None,
            'founder_id': user['id']
        }
        
        # Save to Firestore
        if firebase_service.db:
            doc_ref = firebase_service.db.collection('startup_submissions').add(submission_data)
            submission_id = doc_ref[1].id
        else:
            submission_id = f"temp_{uuid.uuid4().hex[:8]}"
        
        # Create clean response data without SERVER_TIMESTAMP objects
        response_data = {
            'id': submission_id,
            'startupId': startup_id,
            'status': 'awaiting_uploads',
            'processingStage': 'awaiting_assets',
            'submission': {
                'startupName': submission_data['submission']['startupName'],
                'description': submission_data['submission']['description'],
                'location': submission_data['submission']['location'],
                'foundingDate': submission_data['submission']['foundingDate']
            }
        }
        
        logger.info(f"Startup submission created: {startup_id} by {user['email']}")
        return APIResponse.success(
            data=response_data,
            message='Startup submission created successfully'
        )
    
    except Exception as e:
        logger.exception(f"Error creating startup submission: {e}")
        return APIResponse.server_error('Failed to create startup submission')


@founder_bp.route('/api/startup-submission/<submission_id>/upload', methods=['POST'])
@login_required
@founder_required
@handle_api_exception
def upload_file_to_submission(submission_id):
    """Upload file to startup submission"""
    try:
        user = get_current_user()
        logger.info(f"Upload request from user {user['email']} for submission {submission_id}")
        
        if not user:
            return APIResponse.unauthorized('User not found')
        
        if not firebase_service.db:
            return APIResponse.server_error('Database not available')
        
        # Check if submission exists and belongs to user
        submission_ref = firebase_service.db.collection('startup_submissions').document(submission_id)
        submission_doc = submission_ref.get()
        
        if not submission_doc.exists:
            return APIResponse.not_found('Startup submission not found')
        
        submission_data = submission_doc.to_dict()
        if submission_data['founder_id'] != user['id']:
            return APIResponse.forbidden('You can only upload files to your own submissions')
        
        # Get file and file type from request
        if 'file' not in request.files:
            logger.error("No file in request")
            return APIResponse.validation_error({'file': 'No file provided'})
        
        file = request.files['file']
        file_type = request.form.get('file_type', 'document')
        
        logger.info(f"File received: {file.filename}, type: {file_type}")
        
        if file.filename == '':
            return APIResponse.validation_error({'file': 'No file selected'})
        
        # Determine identifier for filenames and storage context
        startup_identifier = (
            submission_data.get('startupId')
            or submission_data.get('submission', {}).get('startupId')
            or submission_id
        )

        # Save file
        file_result = file_upload_service.save_file(file, file_type, startup_identifier)
        
        if not file_result['valid']:
            return APIResponse.validation_error({'file': file_result['error']})
        
        # Add file info to submission
        asset_info = {
            'type': file_type,
            'filename': file_result['filename'],
            'original_filename': file_result['original_filename'],
            'url': file_result['url'],
            'file_path': file_result['file_path'],
            'file_size': file_result['file_size'],
            'mime_type': file_result['mime_type'],
            'uploaded_at': datetime.now(timezone.utc).isoformat()
        }
        
        # Update submission with new asset, using ArrayUnion to avoid race conditions
        submission_ref.update({
            'submission.uploadedAssets': firestore.ArrayUnion([asset_info]),
            'updated_at': firestore.SERVER_TIMESTAMP
        })
        
        logger.info(f"File uploaded to submission {submission_id}: {file_result['filename']}")
        return APIResponse.success(
            data=asset_info,
            message='File uploaded successfully'
        )
    
    except Exception as e:
        logger.exception(f"Error uploading file: {e}")
        return APIResponse.server_error('Failed to upload file')


@founder_bp.route('/api/startup-submission/<submission_id>/process', methods=['POST'])
@login_required
@founder_required
@handle_api_exception
def trigger_submission_processing(submission_id):
    """Finalize uploads and queue the submission for AI processing"""
    try:
        user = get_current_user()

        if not user:
            return APIResponse.unauthorized('User not found')

        if not firebase_service.db:
            return APIResponse.server_error('Database not available')

        submission_ref = firebase_service.db.collection('startup_submissions').document(submission_id)
        submission_doc = submission_ref.get()

        if not submission_doc.exists:
            return APIResponse.not_found('Startup submission not found')

        submission_data = submission_doc.to_dict()
        if submission_data.get('founder_id') != user['id']:
            return APIResponse.forbidden('You can only process your own submissions')

        uploaded_assets = submission_data.get('submission', {}).get('uploadedAssets', [])
        if not uploaded_assets:
            return APIResponse.validation_error({'uploadedAssets': 'Please upload at least one supporting file before processing'})

        # Update status to queued for processing
        submission_ref.update({
            'status': 'queued',
            'processingStage': 'queued_for_processing',
            'updated_at': firestore.SERVER_TIMESTAMP
        })

        # Queue submission with latest data snapshot
        queued = processing_pipeline.queue_submission(submission_id, submission_data)
        if not queued:
            submission_ref.update({
                'status': 'awaiting_uploads',
                'processingStage': 'awaiting_assets',
                'updated_at': firestore.SERVER_TIMESTAMP
            })
            return APIResponse.server_error('Submission could not be queued. Please try again shortly.')

        logger.info(f"Submission {submission_id} queued for AI processing by {user['email']}")
        return APIResponse.success(message='Submission queued for processing')

    except Exception as e:
        logger.exception(f"Error queueing submission {submission_id} for processing: {e}")
        return APIResponse.server_error('Failed to queue submission for processing')


@founder_bp.route('/api/startup-submission/<submission_id>/file/<asset_index>', methods=['DELETE'])
@login_required
@founder_required
@handle_api_exception
def delete_file_from_submission(submission_id, asset_index):
    """Delete file from startup submission"""
    try:
        user = get_current_user()
        
        if not user:
            return APIResponse.unauthorized('User not found')
        
        if not firebase_service.db:
            return APIResponse.server_error('Database not available')
        
        # Check if submission exists and belongs to user
        submission_ref = firebase_service.db.collection('startup_submissions').document(submission_id)
        submission_doc = submission_ref.get()
        
        if not submission_doc.exists:
            return APIResponse.not_found('Startup submission not found')
        
        submission_data = submission_doc.to_dict()
        if submission_data['founder_id'] != user['id']:
            return APIResponse.forbidden('You can only delete files from your own submissions')
        
        # Get asset index
        try:
            asset_index = int(asset_index)
        except ValueError:
            return APIResponse.validation_error({'asset_index': 'Invalid asset index'})
        
        uploaded_assets = submission_data['submission']['uploadedAssets']
        if asset_index >= len(uploaded_assets):
            return APIResponse.not_found('File not found')
        
        # Get asset to delete
        asset = uploaded_assets[asset_index]
        
        # Delete file from filesystem
        if 'file_path' in asset:
            file_upload_service.delete_file(asset['file_path'])
        
        # Remove asset from submission
        uploaded_assets.pop(asset_index)
        
        # Update submission
        submission_ref.update({
            'submission.uploadedAssets': uploaded_assets,
            'updated_at': firestore.SERVER_TIMESTAMP
        })
        
        logger.info(f"File deleted from submission {submission_id}: {asset.get('filename', 'unknown')}")
        return APIResponse.success(message='File deleted successfully')
    
    except Exception as e:
        logger.exception(f"Error deleting file: {e}")
        return APIResponse.server_error('Failed to delete file')


@founder_bp.route('/api/startup-submissions')
@login_required
@founder_required
@handle_api_exception
def get_startup_submissions():
    """Get all startup submissions for the current founder"""
    try:
        user = get_current_user()
        
        if not user:
            return APIResponse.unauthorized('User not found')
        
        if not firebase_service.db:
            return APIResponse.server_error('Database not available')
        
        # Get founder's submissions
        submissions_ref = firebase_service.db.collection('startup_submissions').where('founder_id', '==', user['id'])
        submissions_docs = submissions_ref.stream()
        
        submissions = []
        for doc in submissions_docs:
            data = {'id': doc.id, **doc.to_dict()}
            data['created_at_display'] = _format_timestamp(data.get('created_at'))
            data['updated_at_display'] = _format_timestamp(data.get('updated_at'))
            submissions.append(data)
        
        # Sort by creation date (newest first)
        submissions.sort(key=lambda x: x.get('created_at', datetime.min), reverse=True)
        
        return APIResponse.success(data=submissions)
    
    except Exception as e:
        logger.exception(f"Error fetching startup submissions: {e}")
        return APIResponse.server_error('Failed to fetch startup submissions')


@founder_bp.route('/api/startup-submission/<submission_id>', methods=['GET'])
@login_required
@founder_required
@handle_api_exception
def get_startup_submission(submission_id):
    """Get single startup submission details"""
    try:
        user = get_current_user()
        
        if not user:
            return APIResponse.unauthorized('User not found')
        
        if not firebase_service.db:
            return APIResponse.server_error('Database not available')
        
        # Get submission
        submission_ref = firebase_service.db.collection('startup_submissions').document(submission_id)
        submission_doc = submission_ref.get()
        
        if not submission_doc.exists:
            return APIResponse.not_found('Startup submission not found')
        
        submission_data = submission_doc.to_dict()
        
        # Check if user owns this submission
        if submission_data.get('founder_id') != user['id']:
            return APIResponse.forbidden('Access denied')
        
        # Convert SERVER_TIMESTAMP to string for JSON serialization
        if 'created_at' in submission_data and hasattr(submission_data['created_at'], 'timestamp'):
            submission_data['created_at'] = submission_data['created_at'].timestamp()
        if 'updated_at' in submission_data and hasattr(submission_data['updated_at'], 'timestamp'):
            submission_data['updated_at'] = submission_data['updated_at'].timestamp()
        
        logger.info(f"Startup submission retrieved: {submission_id} by {user['email']}")
        return APIResponse.success(data=submission_data, message='Startup submission retrieved successfully')
        
    except Exception as e:
        logger.exception(f"Error retrieving startup submission: {e}")
        return APIResponse.server_error('Failed to retrieve startup submission')


@founder_bp.route('/api/startup-submission/<submission_id>', methods=['DELETE'])
@login_required
@founder_required
@handle_api_exception
def delete_startup_submission(submission_id):
    """Delete startup submission"""
    try:
        user = get_current_user()
        
        if not user:
            return APIResponse.unauthorized('User not found')
        
        if not firebase_service.db:
            return APIResponse.server_error('Database not available')
        
        # Check if submission exists and belongs to user
        submission_ref = firebase_service.db.collection('startup_submissions').document(submission_id)
        submission_doc = submission_ref.get()
        
        if not submission_doc.exists:
            return APIResponse.not_found('Startup submission not found')
        
        submission_data = submission_doc.to_dict()
        if submission_data['founder_id'] != user['id']:
            return APIResponse.forbidden('You can only delete your own submissions')
        
        # Delete associated files
        if 'submission' in submission_data and 'uploadedAssets' in submission_data['submission']:
            for asset in submission_data['submission']['uploadedAssets']:
                if 'file_path' in asset:
                    file_upload_service.delete_file(asset['file_path'])
        
        # Delete submission
        submission_ref.delete()
        
        logger.info(f"Startup submission deleted: {submission_id} by {user['email']}")
        return APIResponse.success(message='Startup submission deleted successfully')
    
    except Exception as e:
        logger.exception(f"Error deleting startup submission: {e}")
        return APIResponse.server_error('Failed to delete startup submission')
