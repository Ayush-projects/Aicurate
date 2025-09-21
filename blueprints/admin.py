"""
Admin blueprint for AI Investment Platform
Handles all admin-specific routes and functionality
"""

from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from utils.auth import login_required, admin_required, get_current_user
from utils.api import APIResponse, handle_api_exception
from utils.validation import validate_required_fields, InputValidator
from services.firebase_service import firebase_service
import logging

logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin', __name__)


def _format_timestamp(value):
    """Return human readable timestamp string for templates."""
    if isinstance(value, datetime):
        return value.strftime('%Y-%m-%d %H:%M')
    return None


@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Admin dashboard"""
    try:
        user = get_current_user()
        if not user:
            flash('User data not found', 'error')
            return redirect(url_for('auth.login'))
        
        # Get statistics
        stats = {
            'total_users': 0,
            'total_startups': 0,
            'total_investments': 0,
            'total_investment_amount': 0
        }
        
        if firebase_service.db:
            try:
                # Count users
                users_ref = firebase_service.db.collection('users')
                stats['total_users'] = len(list(users_ref.stream()))
                
                # Count startups
                startups_ref = firebase_service.db.collection('startups')
                stats['total_startups'] = len(list(startups_ref.stream()))
                
                # Count investments and calculate total amount
                investments_ref = firebase_service.db.collection('investments')
                investments = list(investments_ref.stream())
                stats['total_investments'] = len(investments)
                stats['total_investment_amount'] = sum(
                    doc.to_dict().get('amount', 0) for doc in investments
                )
                
            except Exception as e:
                logger.error(f"Error fetching statistics: {e}")
                flash('Error loading statistics', 'error')
        
        return render_template(
            'admin/dashboard.html',
            user=user,
            stats=stats,
            firestore_enabled=bool(firebase_service.db)
        )
    
    except Exception as e:
        logger.exception(f"Error in admin dashboard: {e}")
        flash('An error occurred while loading the dashboard', 'error')
        return redirect(url_for('home'))


@admin_bp.route('/users')
@login_required
@admin_required
def users():
    """User management page"""
    try:
        user = get_current_user()
        if not user:
            flash('User data not found', 'error')
            return redirect(url_for('auth.login'))
        
        # Get all users
        users = []
        if firebase_service.db:
            try:
                users_ref = firebase_service.db.collection('users')
                users_docs = users_ref.stream()
                for doc in users_docs:
                    data = {'id': doc.id, **doc.to_dict()}
                    data['created_at_display'] = _format_timestamp(data.get('created_at'))
                    data['updated_at_display'] = _format_timestamp(data.get('updated_at'))
                    users.append(data)
            except Exception as e:
                logger.error(f"Error fetching users: {e}")
                flash('Error loading users', 'error')
        
        return render_template(
            'admin/users.html',
            user=user,
            users=users,
            firestore_enabled=bool(firebase_service.db)
        )
    
    except Exception as e:
        logger.exception(f"Error in admin users: {e}")
        flash('An error occurred while loading users', 'error')
        return redirect(url_for('admin.dashboard'))


@admin_bp.route('/startups')
@login_required
@admin_required
def startups():
    """Startup management page"""
    try:
        user = get_current_user()
        if not user:
            flash('User data not found', 'error')
            return redirect(url_for('auth.login'))
        
        # Get all startups
        startups = []
        if firebase_service.db:
            try:
                startups_ref = firebase_service.db.collection('startups')
                startups_docs = startups_ref.stream()
                for doc in startups_docs:
                    data = {'id': doc.id, **doc.to_dict()}
                    data['created_at_display'] = _format_timestamp(data.get('created_at'))
                    data['updated_at_display'] = _format_timestamp(data.get('updated_at'))
                    startups.append(data)
            except Exception as e:
                logger.error(f"Error fetching startups: {e}")
                flash('Error loading startups', 'error')

        total_goal = sum(float(startup.get('funding_goal') or 0) for startup in startups)

        return render_template(
            'admin/startups.html',
            user=user,
            startups=startups,
            total_goal=total_goal,
            firestore_enabled=bool(firebase_service.db)
        )
    
    except Exception as e:
        logger.exception(f"Error in admin startups: {e}")
        flash('An error occurred while loading startups', 'error')
        return redirect(url_for('admin.dashboard'))


@admin_bp.route('/investments')
@login_required
@admin_required
def investments():
    """Investment management page"""
    try:
        user = get_current_user()
        if not user:
            flash('User data not found', 'error')
            return redirect(url_for('auth.login'))
        
        # Get all investments
        investments = []
        if firebase_service.db:
            try:
                investments_ref = firebase_service.db.collection('investments')
                investments_docs = investments_ref.stream()
                for doc in investments_docs:
                    data = {'id': doc.id, **doc.to_dict()}
                    data['created_at_display'] = _format_timestamp(data.get('created_at'))
                    data['updated_at_display'] = _format_timestamp(data.get('updated_at'))
                    investments.append(data)
            except Exception as e:
                logger.error(f"Error fetching investments: {e}")
                flash('Error loading investments', 'error')

        total_amount = sum(float(investment.get('amount') or 0) for investment in investments)

        return render_template(
            'admin/investments.html',
            user=user,
            investments=investments,
            total_amount=total_amount,
            firestore_enabled=bool(firebase_service.db)
        )
    
    except Exception as e:
        logger.exception(f"Error in admin investments: {e}")
        flash('An error occurred while loading investments', 'error')
        return redirect(url_for('admin.dashboard'))


@admin_bp.route('/api/user/<user_id>/status', methods=['PUT'])
@login_required
@admin_required
@handle_api_exception
def update_user_status(user_id):
    """Update user status (active/inactive)"""
    try:
        data = request.get_json()
        user = get_current_user()
        
        if not user:
            return APIResponse.unauthorized('User not found')
        
        if not firebase_service.db:
            return APIResponse.server_error('Database not available')
        
        # Validate status
        status = data.get('status')
        if status not in ['active', 'inactive']:
            return APIResponse.validation_error({'status': 'Invalid status. Must be active or inactive'})
        
        # Check if user exists
        user_ref = firebase_service.db.collection('users').document(user_id)
        user_doc = user_ref.get()
        
        if not user_doc.exists:
            return APIResponse.not_found('User not found')
        
        # Update user status
        user_ref.update({
            'active': status == 'active',
            'updated_at': firebase_service.db.SERVER_TIMESTAMP
        })
        
        logger.info(f"User status updated: {user_id} to {status} by {user['email']}")
        return APIResponse.success(message=f'User status updated to {status}')
    
    except Exception as e:
        logger.exception(f"Error updating user status: {e}")
        return APIResponse.server_error('Failed to update user status')


@admin_bp.route('/api/startup/<startup_id>/status', methods=['PUT'])
@login_required
@admin_required
@handle_api_exception
def update_startup_status(startup_id):
    """Update startup status"""
    try:
        data = request.get_json()
        user = get_current_user()
        
        if not user:
            return APIResponse.unauthorized('User not found')
        
        if not firebase_service.db:
            return APIResponse.server_error('Database not available')
        
        # Validate status
        status = data.get('status')
        valid_statuses = ['active', 'inactive', 'funded', 'rejected']
        if status not in valid_statuses:
            return APIResponse.validation_error({'status': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'})
        
        # Check if startup exists
        startup_ref = firebase_service.db.collection('startups').document(startup_id)
        startup_doc = startup_ref.get()
        
        if not startup_doc.exists:
            return APIResponse.not_found('Startup not found')
        
        # Update startup status
        startup_ref.update({
            'status': status,
            'updated_at': firebase_service.db.SERVER_TIMESTAMP
        })
        
        logger.info(f"Startup status updated: {startup_id} to {status} by {user['email']}")
        return APIResponse.success(message=f'Startup status updated to {status}')
    
    except Exception as e:
        logger.exception(f"Error updating startup status: {e}")
        return APIResponse.server_error('Failed to update startup status')


@admin_bp.route('/api/investment/<investment_id>/status', methods=['PUT'])
@login_required
@admin_required
@handle_api_exception
def update_investment_status(investment_id):
    """Update investment status"""
    try:
        data = request.get_json()
        user = get_current_user()
        
        if not user:
            return APIResponse.unauthorized('User not found')
        
        if not firebase_service.db:
            return APIResponse.server_error('Database not available')
        
        # Validate status
        status = data.get('status')
        valid_statuses = ['pending', 'approved', 'rejected', 'completed']
        if status not in valid_statuses:
            return APIResponse.validation_error({'status': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'})
        
        # Check if investment exists
        investment_ref = firebase_service.db.collection('investments').document(investment_id)
        investment_doc = investment_ref.get()
        
        if not investment_doc.exists:
            return APIResponse.not_found('Investment not found')
        
        # Update investment status
        investment_ref.update({
            'status': status,
            'updated_at': firebase_service.db.SERVER_TIMESTAMP
        })
        
        logger.info(f"Investment status updated: {investment_id} to {status} by {user['email']}")
        return APIResponse.success(message=f'Investment status updated to {status}')
    
    except Exception as e:
        logger.exception(f"Error updating investment status: {e}")
        return APIResponse.server_error('Failed to update investment status')


@admin_bp.route('/api/delete/<collection>/<doc_id>', methods=['DELETE'])
@login_required
@admin_required
@handle_api_exception
def delete_document(collection, doc_id):
    """Delete document from any collection (admin only)"""
    try:
        user = get_current_user()
        
        if not user:
            return APIResponse.unauthorized('User not found')
        
        if not firebase_service.db:
            return APIResponse.server_error('Database not available')
        
        # Validate collection
        valid_collections = ['users', 'startups', 'investments']
        if collection not in valid_collections:
            return APIResponse.validation_error({'collection': f'Invalid collection. Must be one of: {", ".join(valid_collections)}'})
        
        # Check if document exists
        doc_ref = firebase_service.db.collection(collection).document(doc_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            return APIResponse.not_found(f'{collection.title()} not found')
        
        # Delete document
        doc_ref.delete()
        
        logger.info(f"Document deleted: {collection}/{doc_id} by {user['email']}")
        return APIResponse.success(message=f'{collection.title()} deleted successfully')
    
    except Exception as e:
        logger.exception(f"Error deleting document: {e}")
        return APIResponse.server_error('Failed to delete document')
