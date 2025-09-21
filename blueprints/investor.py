"""
Investor blueprint for AI Investment Platform
Handles all investor-specific routes and functionality
"""

from datetime import datetime, timezone
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from utils.auth import login_required, investor_required, get_current_user
from utils.api import APIResponse, handle_api_exception
from utils.validation import validate_required_fields, InputValidator
from services.firebase_service import firebase_service
from services.reranking_service import reranking_service
from firebase_admin import firestore
import logging

logger = logging.getLogger(__name__)

investor_bp = Blueprint('investor', __name__)


def _format_timestamp(value):
    """Return a readable timestamp for templates."""
    if isinstance(value, datetime):
        return value.strftime('%Y-%m-%d %H:%M')
    return None


def _sort_timestamp(primary, fallback):
    """Return comparable timestamp for ordering."""
    candidate = primary if isinstance(primary, datetime) else fallback if isinstance(fallback, datetime) else None
    if candidate:
        return candidate
    return datetime.fromtimestamp(0, tz=timezone.utc)


@investor_bp.route('/dashboard')
@login_required
@investor_required
def dashboard():
    """Investor dashboard"""
    try:
        user = get_current_user()
        if not user:
            flash('User data not found', 'error')
            return redirect(url_for('auth.login'))
        
        # Get available startups for investment from startup_evaluation_reports
        startups = []
        if firebase_service.db:
            try:
                reports_ref = firebase_service.db.collection('startup_evaluation_reports')
                reports_docs = reports_ref.stream()
                
                for doc in reports_docs:
                    report_data = doc.to_dict()
                    # Map the report data to dashboard format
                    startup_data = {
                        'startup_id': doc.id,
                        'startup_name': report_data.get('submission', {}).get('startupName', 'Unnamed Startup'),
                        'sector': report_data.get('companyProfile', {}).get('sector', 'Technology'),
                        'description': report_data.get('companyProfile', {}).get('description', 'A promising startup with innovative solutions.'),
                        'overall_score': report_data.get('scores', {}).get('OverallScore', 0),
                        'financials': report_data.get('financials', {}),
                        'created_at_display': _format_timestamp(report_data.get('submittedAt')),
                        'updated_at_display': _format_timestamp(report_data.get('submittedAt'))
                    }
                    startups.append(startup_data)
                    
            except Exception as e:
                logger.error(f"Error fetching startup reports: {e}")
                flash('Error loading startup data', 'error')
        
        # If no startups found in Firestore, use fallback data
        if not startups:
            import json
            import os
            
            report_path = os.path.join(os.path.dirname(__file__), '..', 'models', 'startup_evaluation_report.json')
            
            try:
                with open(report_path, 'r') as f:
                    report_data = json.load(f)
                    # Add the main startup from JSON
                    startup_data = {
                        'startup_id': 'FUFQwvVdetdOc0J19EkoL',
                        'startup_name': report_data.get('submission', {}).get('startupName', 'Kredily'),
                        'sector': report_data.get('companyProfile', {}).get('sector', 'HR Tech'),
                        'description': report_data.get('companyProfile', {}).get('description', 'A comprehensive HR management platform.'),
                        'overall_score': report_data.get('scores', {}).get('OverallScore', 7.9),
                        'financials': report_data.get('financials', {}),
                        'created_at_display': '2024-01-15 10:30',
                        'updated_at_display': '2024-01-15 10:30'
                    }
                    startups.append(startup_data)
                    
                    # Add some additional sample startups for demo
                    sample_startups = [
                        {
                            'startup_id': 'strp_002',
                            'startup_name': 'MediTech Solutions',
                            'sector': 'Healthtech',
                            'description': 'AI-powered diagnostic tools for early disease detection and personalized treatment recommendations.',
                            'overall_score': 8.2,
                            'financials': {'fundingRequiredINR': 15000000},
                            'created_at_display': '2024-01-20 14:15',
                            'updated_at_display': '2024-01-20 14:15'
                        },
                        {
                            'startup_id': 'strp_003',
                            'startup_name': 'EduFlow',
                            'sector': 'Edtech',
                            'description': 'Interactive learning platform with AI tutoring and personalized curriculum for students.',
                            'overall_score': 7.5,
                            'financials': {'fundingRequiredINR': 8000000},
                            'created_at_display': '2024-01-18 09:45',
                            'updated_at_display': '2024-01-18 09:45'
                        },
                        {
                            'startup_id': 'strp_004',
                            'startup_name': 'GreenEnergy Pro',
                            'sector': 'CleanTech',
                            'description': 'Smart energy management systems for residential and commercial buildings.',
                            'overall_score': 8.7,
                            'financials': {'fundingRequiredINR': 25000000},
                            'created_at_display': '2024-01-22 16:20',
                            'updated_at_display': '2024-01-22 16:20'
                        },
                        {
                            'startup_id': 'strp_005',
                            'startup_name': 'FinSecure',
                            'sector': 'Fintech',
                            'description': 'Blockchain-based secure payment gateway with fraud detection and compliance tools.',
                            'overall_score': 7.8,
                            'financials': {'fundingRequiredINR': 12000000},
                            'created_at_display': '2024-01-19 11:30',
                            'updated_at_display': '2024-01-19 11:30'
                        },
                        {
                            'startup_id': 'strp_006',
                            'startup_name': 'AgriTech Innovations',
                            'sector': 'AgriTech',
                            'description': 'IoT sensors and AI analytics for precision farming and crop optimization.',
                            'overall_score': 8.1,
                            'financials': {'fundingRequiredINR': 18000000},
                            'created_at_display': '2024-01-21 13:10',
                            'updated_at_display': '2024-01-21 13:10'
                        }
                    ]
                    startups.extend(sample_startups)
                    logger.info("Loaded fallback startup data from JSON file and sample data")
            except Exception as e:
                logger.error(f"Error loading fallback startup data: {e}")

        # Get investor's investments
        investments = []
        if firebase_service.db:
            try:
                investments_ref = firebase_service.db.collection('investments').where('investor_id', '==', user['id'])
                investments_docs = investments_ref.stream()
                for doc in investments_docs:
                    data = {'id': doc.id, **doc.to_dict()}
                    data['created_at_display'] = _format_timestamp(data.get('created_at'))
                    data['updated_at_display'] = _format_timestamp(data.get('updated_at'))
                    investments.append(data)
            except Exception as e:
                logger.error(f"Error fetching investments: {e}")
                flash('Error loading investment data', 'error')

        total_invested = sum(float(inv.get('amount') or 0) for inv in investments)
        
        # Get accepted and rejected investment counts
        accepted_count = len([inv for inv in investments if inv.get('status') == 'accepted'])
        rejected_count = len([inv for inv in investments if inv.get('status') == 'rejected'])
        
        # Get accepted (interested) startups count
        accepted_interest_count = 0
        rejected_interest_count = 0
        if firebase_service.db:
            try:
                # Count interested as accepted
                interest_ref = firebase_service.db.collection('investor_startup_interest').where('investor_id', '==', user['id']).where('interest_level', '==', 'interested')
                interested_docs = interest_ref.stream()
                accepted_interest_count = len(list(interested_docs))
                
                # Count not_interested as rejected
                rejected_ref = firebase_service.db.collection('investor_startup_interest').where('investor_id', '==', user['id']).where('interest_level', '==', 'not_interested')
                rejected_docs = rejected_ref.stream()
                rejected_interest_count = len(list(rejected_docs))
            except Exception as e:
                logger.error(f"Error fetching interested startups: {e}")
        
        stats = {
            'total_investments': len(investments),
            'total_invested': total_invested,
            'active_startups': len(startups),
            'average_investment': (total_invested / len(investments)) if investments else 0,
            'accepted_count': accepted_count + accepted_interest_count,  # Combine investment accepts + interest accepts
            'rejected_count': rejected_count + rejected_interest_count,  # Combine investment rejects + interest rejects
            'interested_count': accepted_interest_count  # Keep for backward compatibility
        }

        recent_investments = sorted(
            investments,
            key=lambda inv: _sort_timestamp(inv.get('updated_at'), inv.get('created_at')),
            reverse=True
        )[:5]

        return render_template(
            'investor/dashboard.html',
            user=user,
            startups=startups,
            investments=investments,
            stats=stats,
            recent_investments=recent_investments,
            firestore_enabled=bool(firebase_service.db)
        )
    
    except Exception as e:
        logger.exception(f"Error in investor dashboard: {e}")
        flash('An error occurred while loading the dashboard', 'error')
        return redirect(url_for('home'))


@investor_bp.route('/preferences')
@login_required
@investor_required
def preferences():
    """Investment preferences page for investors"""
    try:
        user = get_current_user()
        if not user:
            flash('User data not found', 'error')
            return redirect(url_for('auth.login'))

        return render_template(
            'investor/preferences.html',
            user=user,
            firestore_enabled=bool(firebase_service.db)
        )

    except Exception as e:
        logger.exception(f"Error in investor preferences: {e}")
        flash('An error occurred while loading preferences', 'error')
        return redirect(url_for('investor.dashboard'))


@investor_bp.route('/profile')
@login_required
@investor_required
def profile():
    """Investor profile page"""
    try:
        user = get_current_user()
        if not user:
            flash('User data not found', 'error')
            return redirect(url_for('auth.login'))
        
        return render_template(
            'investor/profile.html',
            user=user,
            firestore_enabled=bool(firebase_service.db)
        )
    
    except Exception as e:
        logger.exception(f"Error in investor profile: {e}")
        flash('An error occurred while loading the profile', 'error')
        return redirect(url_for('investor.dashboard'))


@investor_bp.route('/startups')
@login_required
@investor_required
def startups():
    """Available startups for investment"""
    try:
        user = get_current_user()
        if not user:
            flash('User data not found', 'error')
            return redirect(url_for('auth.login'))
        
        # Get available startups
        startups = []
        if firebase_service.db:
            try:
                startups_ref = firebase_service.db.collection('startups').where('status', '==', 'active')
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
            'investor/startups.html',
            user=user,
            startups=startups,
            firestore_enabled=bool(firebase_service.db)
        )
    
    except Exception as e:
        logger.exception(f"Error in investor startups: {e}")
        flash('An error occurred while loading startups', 'error')
        return redirect(url_for('investor.dashboard'))


@investor_bp.route('/investments')
@login_required
@investor_required
def investments():
    """Investor's investments"""
    try:
        user = get_current_user()
        if not user:
            flash('User data not found', 'error')
            return redirect(url_for('auth.login'))
        
        # Get investor's investments
        investments = []
        if firebase_service.db:
            try:
                investments_ref = firebase_service.db.collection('investments').where('investor_id', '==', user['id'])
                investments_docs = investments_ref.stream()
                for doc in investments_docs:
                    data = {'id': doc.id, **doc.to_dict()}
                    data['created_at_display'] = _format_timestamp(data.get('created_at'))
                    data['updated_at_display'] = _format_timestamp(data.get('updated_at'))
                    investments.append(data)
            except Exception as e:
                logger.error(f"Error fetching investments: {e}")
                flash('Error loading investments', 'error')

        total_invested = sum(float(inv.get('amount') or 0) for inv in investments)

        return render_template(
            'investor/investments.html',
            user=user,
            investments=investments,
            total_invested=total_invested,
            firestore_enabled=bool(firebase_service.db)
        )
    
    except Exception as e:
        logger.exception(f"Error in investor investments: {e}")
        flash('An error occurred while loading investments', 'error')
        return redirect(url_for('investor.dashboard'))


@investor_bp.route('/api/preferences', methods=['GET', 'PUT'])
@login_required
@investor_required
@handle_api_exception
def investor_preferences():
    """Get or update investor preferences."""
    try:
        user = get_current_user()
        if not user:
            return APIResponse.unauthorized('User not found')

        uid = user['id']

        if request.method == 'GET':
            # Fetch preferences from Firestore
            if not firebase_service.db:
                return APIResponse.server_error('Database not available')

            user_doc = firebase_service.db.collection('users').document(uid).get()
            if not user_doc.exists:
                return APIResponse.not_found('User profile not found')

            prefs = user_doc.to_dict().get('preferences', {})
            return APIResponse.success(data=prefs)

        # PUT (update)
        data = request.get_json() or {}

        # Basic validation – ensure numeric fields are valid floats/ints and required list fields are lists.
        errors = {}

        # Validate ticket sizes if provided
        ticket_min = data.get('ticket_size_min')
        ticket_max = data.get('ticket_size_max')
        if ticket_min is not None and not InputValidator.validate_funding_amount(ticket_min):
            errors['ticket_size_min'] = 'Invalid minimum ticket size'
        if ticket_max is not None and not InputValidator.validate_funding_amount(ticket_max):
            errors['ticket_size_max'] = 'Invalid maximum ticket size'
        if ticket_min is not None and ticket_max is not None:
            try:
                if float(ticket_min) > float(ticket_max):
                    errors['ticket_size'] = 'Minimum ticket size cannot exceed maximum ticket size'
            except ValueError:
                errors['ticket_size'] = 'Ticket sizes must be numeric'

        # Ensure list-based preferences are lists when present
        list_fields = [
            'sectors', 'investment_stage', 'geography', 'business_model', 'funding_types',
        ]
        for field in list_fields:
            if field in data and not isinstance(data[field], list):
                errors[field] = 'Must be an array'

        if errors:
            return APIResponse.validation_error(errors)

        update_payload = {
            'preferences': data,
            'profile_complete': True,
        }

        # Update Firestore
        if not firebase_service.update_user_profile(uid, update_payload):
            return APIResponse.server_error('Failed to update preferences')

        # Update session with new preferences for immediate availability in templates
        from utils.auth import update_session_profile
        update_session_profile(update_payload)

        # Invalidate cache for this investor since preferences changed
        try:
            reranking_service.invalidate_cache_for_investor(uid)
        except Exception as e:
            logger.error(f"Error invalidating cache after preference update: {e}")
        
        # Trigger reranking with new preferences
        try:
            reranking_result = reranking_service.trigger_reranking_on_preference_change(uid)
            if not reranking_result.get('success'):
                logger.warning(f"Reranking failed after preference update: {reranking_result.get('message')}")
        except Exception as e:
            logger.error(f"Error triggering reranking after preference update: {e}")

        return APIResponse.success(message='Preferences updated successfully', data=data)

    except Exception as exc:
        import logging
        logging.exception("Error in investor_preferences API: %s", exc)
        return APIResponse.server_error('An unexpected error occurred')


# ---------------- Existing investment routes below ----------------

@investor_bp.route('/api/invest', methods=['POST'])
@login_required
@investor_required
@handle_api_exception
def create_investment():
    """Create new investment"""
    try:
        data = request.get_json()
        user = get_current_user()
        
        if not user:
            return APIResponse.unauthorized('User not found')
        
        # Validate required fields
        required_fields = ['startup_id', 'amount', 'investment_type']
        validation_errors = validate_required_fields(data, required_fields)
        
        if validation_errors:
            return APIResponse.validation_error(validation_errors)
        
        # Validate investment amount
        if not InputValidator.validate_funding_amount(data['amount']):
            validation_errors['amount'] = 'Invalid investment amount'
        
        # Validate investment type
        valid_types = ['equity', 'debt', 'convertible_note', 'grant']
        if data['investment_type'] not in valid_types:
            validation_errors['investment_type'] = 'Invalid investment type'
        
        if validation_errors:
            return APIResponse.validation_error(validation_errors)
        
        if not firebase_service.db:
            return APIResponse.server_error('Database not available')
        
        # Check if startup exists
        startup_ref = firebase_service.db.collection('startups').document(data['startup_id'])
        startup_doc = startup_ref.get()
        
        if not startup_doc.exists:
            return APIResponse.not_found('Startup not found')
        
        startup_data = startup_doc.to_dict()
        
        # Check if startup is active
        if startup_data.get('status') != 'active':
            return APIResponse.error('Startup is not accepting investments', 400)
        
        # Create investment data
        investment_data = {
            'startup_id': data['startup_id'],
            'startup_name': startup_data['name'],
            'investor_id': user['id'],
            'investor_email': user['email'],
            'amount': float(data['amount']),
            'investment_type': data['investment_type'],
            'status': 'pending',
            'notes': InputValidator.sanitize_input(data.get('notes', '')),
            'created_at': firebase_service.db.SERVER_TIMESTAMP,
            'updated_at': firebase_service.db.SERVER_TIMESTAMP
        }
        
        # Save investment to Firestore
        doc_ref = firebase_service.db.collection('investments').add(investment_data)
        investment_data['id'] = doc_ref[1].id
        
        logger.info(f"Investment created: ${investment_data['amount']} in {startup_data['name']} by {user['email']}")
        return APIResponse.success(
            data=investment_data,
            message='Investment proposal submitted successfully'
        )
    
    except Exception as e:
        logger.exception(f"Error creating investment: {e}")
        return APIResponse.server_error('Failed to create investment')


@investor_bp.route('/api/investment/<investment_id>', methods=['PUT'])
@login_required
@investor_required
@handle_api_exception
def update_investment(investment_id):
    """Update investment"""
    try:
        data = request.get_json()
        user = get_current_user()
        
        if not user:
            return APIResponse.unauthorized('User not found')
        
        if not firebase_service.db:
            return APIResponse.server_error('Database not available')
        
        # Check if investment exists and belongs to user
        investment_ref = firebase_service.db.collection('investments').document(investment_id)
        investment_doc = investment_ref.get()
        
        if not investment_doc.exists:
            return APIResponse.not_found('Investment not found')
        
        investment_data = investment_doc.to_dict()
        if investment_data['investor_id'] != user['id']:
            return APIResponse.forbidden('You can only update your own investments')
        
        # Check if investment can be updated (only pending investments)
        if investment_data.get('status') != 'pending':
            return APIResponse.error('Only pending investments can be updated', 400)
        
        # Validate and sanitize update data
        update_data = {}
        for field in ['amount', 'investment_type', 'notes']:
            if field in data:
                if field == 'amount':
                    if not InputValidator.validate_funding_amount(data[field]):
                        return APIResponse.validation_error({field: 'Invalid investment amount'})
                    update_data[field] = float(data[field])
                elif field == 'investment_type':
                    valid_types = ['equity', 'debt', 'convertible_note', 'grant']
                    if data[field] not in valid_types:
                        return APIResponse.validation_error({field: 'Invalid investment type'})
                    update_data[field] = data[field]
                else:
                    update_data[field] = InputValidator.sanitize_input(data[field])
        
        update_data['updated_at'] = firebase_service.db.SERVER_TIMESTAMP
        
        # Update investment
        investment_ref.update(update_data)
        
        logger.info(f"Investment updated: {investment_id} by {user['email']}")
        return APIResponse.success(message='Investment updated successfully')
    
    except Exception as e:
        logger.exception(f"Error updating investment: {e}")
        return APIResponse.server_error('Failed to update investment')


@investor_bp.route('/api/investment/<investment_id>', methods=['DELETE'])
@login_required
@investor_required
@handle_api_exception
def cancel_investment(investment_id):
    """Cancel investment"""
    try:
        user = get_current_user()
        
        if not user:
            return APIResponse.unauthorized('User not found')
        
        if not firebase_service.db:
            return APIResponse.server_error('Database not available')
        
        # Check if investment exists and belongs to user
        investment_ref = firebase_service.db.collection('investments').document(investment_id)
        investment_doc = investment_ref.get()
        
        if not investment_doc.exists:
            return APIResponse.not_found('Investment not found')
        
        investment_data = investment_doc.to_dict()
        if investment_data['investor_id'] != user['id']:
            return APIResponse.forbidden('You can only cancel your own investments')
        
        # Check if investment can be cancelled (only pending investments)
        if investment_data.get('status') != 'pending':
            return APIResponse.error('Only pending investments can be cancelled', 400)
        
        # Update investment status to cancelled
        investment_ref.update({
            'status': 'cancelled',
            'updated_at': firebase_service.db.SERVER_TIMESTAMP
        })
        
        logger.info(f"Investment cancelled: {investment_id} by {user['email']}")
        return APIResponse.success(message='Investment cancelled successfully')
    
    except Exception as e:
        logger.exception(f"Error cancelling investment: {e}")
        return APIResponse.server_error('Failed to cancel investment')


@investor_bp.route('/deal-insights')
@login_required
@investor_required
def deal_insights():
    """Interactive deal insights dashboard with recommendations"""
    try:
        user = get_current_user()
        if not user:
            flash('User data not found', 'error')
            return redirect(url_for('auth.login'))
        
        # Get investor's recommendations
        recommendations = None
        if firebase_service.db:
            try:
                recommendations = reranking_service.get_investor_recommendations(user['id'])
                logger.info(f"Fetched recommendations for user {user['id']}: {recommendations is not None}")
                if recommendations:
                    logger.info(f"Recommendations contain {len(recommendations.get('rankings', []))} rankings")
            except Exception as e:
                logger.error(f"Error fetching recommendations for user {user['id']}: {e}")
        else:
            logger.warning("Firebase service not available for fetching recommendations")
        
        # Get all startup evaluation reports for the list view
        startup_reports = []
        if firebase_service.db:
            try:
                reports_ref = firebase_service.db.collection('startup_evaluation_reports')
                reports_docs = reports_ref.stream()
                
                for doc in reports_docs:
                    report_data = doc.to_dict()
                    report_data['startup_id'] = doc.id
                    startup_reports.append(report_data)
                
                logger.info(f"Fetched {len(startup_reports)} startup reports from Firestore")
            except Exception as e:
                logger.error(f"Error fetching startup reports: {e}")
        else:
            logger.warning("Firebase service not available for fetching startup reports")
        
        # If no reports in database, use the hardcoded data as fallback
        if not startup_reports:
            logger.info("No startup reports found in Firestore, using fallback data")
            import json
            import os
            
            report_path = os.path.join(os.path.dirname(__file__), '..', 'models', 'startup_evaluation_report.json')
            
            try:
                with open(report_path, 'r') as f:
                    startup_data = json.load(f)
                    startup_data['startup_id'] = 'strp_001'
                    startup_reports = [startup_data]
                logger.info("Loaded fallback data from JSON file")
            except FileNotFoundError:
                # Fallback data if file not found
                startup_reports = [{
                    "startup_id": "strp_001",
                    "submission": {
                        "startupName": "HyperPay",
                        "submittedBy": "founder@hyperpay.com"
                    },
                    "companyProfile": {
                        "description": "AI-driven unified checkout API for Indian and SEA merchants",
                        "sector": "Fintech"
                    },
                    "scores": {
                        "OverallScore": 8.4,
                        "FounderMarketFit": 8.6,
                        "ProductDifferentiation": 8.3,
                        "Traction": 8.1
                    }
                }]
                logger.info("Using hardcoded fallback data")
        
        # Add debug information
        debug_info = {
            'user_id': user['id'],
            'has_recommendations': recommendations is not None,
            'recommendations_count': len(recommendations.get('rankings', [])) if recommendations else 0,
            'startup_reports_count': len(startup_reports),
            'firestore_enabled': bool(firebase_service.db)
        }
        
        return render_template(
            'investor/deal_insights.html',
            user=user,
            startup_reports=startup_reports,
            recommendations=recommendations,
            firestore_enabled=bool(firebase_service.db),
            debug_info=debug_info
        )
    
    except Exception as e:
        logger.exception(f"Error in deal insights: {e}")
        flash('An error occurred while loading the deal insights', 'error')
        return redirect(url_for('investor.dashboard'))


@investor_bp.route('/api/debug/recommendations')
@login_required
@investor_required
def debug_recommendations():
    """Debug endpoint to check recommendation status"""
    try:
        user = get_current_user()
        if not user:
            return jsonify({"error": "User not found"}), 401
        
        debug_info = {
            "user_id": user['id'],
            "firestore_enabled": bool(firebase_service.db),
            "recommendations": None,
            "startup_reports_count": 0,
            "error": None
        }
        
        if firebase_service.db:
            try:
                # Check recommendations
                recommendations = reranking_service.get_investor_recommendations(user['id'])
                debug_info["recommendations"] = recommendations
                
                # Check startup reports
                reports_ref = firebase_service.db.collection('startup_evaluation_reports')
                reports_docs = reports_ref.stream()
                startup_reports = []
                for doc in reports_docs:
                    startup_reports.append(doc.id)
                debug_info["startup_reports_count"] = len(startup_reports)
                debug_info["startup_report_ids"] = startup_reports
                
            except Exception as e:
                debug_info["error"] = str(e)
                logger.error(f"Debug error for user {user['id']}: {e}")
        else:
            debug_info["error"] = "Firebase service not available"
        
        return jsonify(debug_info)
    
    except Exception as e:
        logger.exception(f"Error in debug recommendations: {e}")
        return jsonify({"error": str(e)}), 500


@investor_bp.route('/deal-insights/<startup_id>')
@login_required
@investor_required
def startup_deal_insights(startup_id):
    """Individual startup deal insights page"""
    try:
        user = get_current_user()
        if not user:
            flash('User data not found', 'error')
            return redirect(url_for('auth.login'))
        
        # Get startup evaluation report
        startup_report = None
        if firebase_service.db:
            try:
                report_ref = firebase_service.db.collection('startup_evaluation_reports').document(startup_id)
                report_doc = report_ref.get()
                if report_doc.exists:
                    startup_report = report_doc.to_dict()
                    startup_report['startup_id'] = startup_id
            except Exception as e:
                logger.error(f"Error fetching startup report: {e}")
                flash('Error loading startup data', 'error')
        
        # If no report found in Firebase, try to load from JSON file as fallback
        if not startup_report:
            import json
            import os
            
            report_path = os.path.join(os.path.dirname(__file__), '..', 'models', 'startup_evaluation_report.json')
            
            try:
                with open(report_path, 'r') as f:
                    startup_report = json.load(f)
                    startup_report['startup_id'] = startup_id
                    logger.info(f"Loaded startup report from JSON file for {startup_id}")
            except FileNotFoundError:
                logger.error(f"Startup evaluation report not found for {startup_id}")
                flash('Startup evaluation report not found', 'error')
                return redirect(url_for('investor.deal_insights'))
        
        # Get investor's interest data for this startup
        investor_interest = None
        if firebase_service.db:
            try:
                interest_ref = firebase_service.db.collection('investor_startup_interest').document(f"{user['id']}_{startup_id}")
                interest_doc = interest_ref.get()
                if interest_doc.exists:
                    investor_interest = interest_doc.to_dict()
            except Exception as e:
                logger.error(f"Error fetching investor interest: {e}")
        
        # Get investor's recommendations to find AI reasoning for this startup
        recommendations = None
        ai_reasoning = None
        match_score = None
        ranking = None
        if firebase_service.db:
            try:
                recommendations = reranking_service.get_investor_recommendations(user['id'])
                if recommendations and recommendations.get('rankings'):
                    for rank in recommendations['rankings']:
                        if rank.get('startup_id') == startup_id:
                            ai_reasoning = rank.get('reasoning')
                            match_score = rank.get('match_score')
                            ranking = rank.get('rank')
                            break
            except Exception as e:
                logger.error(f"Error fetching recommendations for startup insights: {e}")
        
        return render_template(
            'investor/startup_deal_insights.html',
            user=user,
            startup_report=startup_report,
            investor_interest=investor_interest,
            ai_reasoning=ai_reasoning,
            match_score=match_score,
            ranking=ranking,
            startup_id=startup_id,
            firestore_enabled=bool(firebase_service.db)
        )
    
    except Exception as e:
        logger.exception(f"Error in startup deal insights: {e}")
        flash('An error occurred while loading the startup insights', 'error')
        return redirect(url_for('investor.dashboard'))


@investor_bp.route('/api/rerank', methods=['POST'])
@login_required
@investor_required
@handle_api_exception
def trigger_reranking():
    """Trigger reranking of startup recommendations"""
    try:
        user = get_current_user()
        if not user:
            return APIResponse.unauthorized('User not found')
        
        result = reranking_service.trigger_reranking_on_preference_change(user['id'])
        
        if result.get('success'):
            return APIResponse.success(
                data=result,
                message='Startup recommendations have been reranked successfully'
            )
        else:
            return APIResponse.server_error(result.get('message', 'Reranking failed'))
    
    except Exception as e:
        logger.exception(f"Error triggering reranking: {e}")
        return APIResponse.server_error('Failed to trigger reranking')


@investor_bp.route('/api/recommendations')
@login_required
@investor_required
@handle_api_exception
def get_recommendations():
    """Get investor's current startup recommendations"""
    try:
        user = get_current_user()
        if not user:
            return APIResponse.unauthorized('User not found')
        
        recommendations = reranking_service.get_investor_recommendations(user['id'])
        
        if recommendations:
            return APIResponse.success(data=recommendations)
        else:
            return APIResponse.not_found('No recommendations found')
    
    except Exception as e:
        logger.exception(f"Error getting recommendations: {e}")
        return APIResponse.server_error('Failed to get recommendations')


@investor_bp.route('/api/startup-interest/<startup_id>', methods=['POST'])
@login_required
@investor_required
@handle_api_exception
def update_startup_interest(startup_id):
    """Update investor's interest level for a startup"""
    try:
        user = get_current_user()
        if not user:
            return APIResponse.unauthorized('User not found')
        
        data = request.get_json() or {}
        interest_level = data.get('interest_level')  # 'interested', 'not_interested', 'neutral'
        
        if not interest_level or interest_level not in ['interested', 'not_interested', 'neutral']:
            return APIResponse.validation_error({'interest_level': 'Invalid interest level'})
        
        if not firebase_service.db:
            return APIResponse.server_error('Database not available')
        
        # Save interest data
        interest_data = {
            'investor_id': user['id'],
            'startup_id': startup_id,
            'interest_level': interest_level,
            'updated_at': firestore.SERVER_TIMESTAMP
        }
        
        interest_ref = firebase_service.db.collection('investor_startup_interest').document(f"{user['id']}_{startup_id}")
        interest_ref.set(interest_data)
        
        # Trigger reranking if preferences changed
        reranking_service.trigger_reranking_on_preference_change(user['id'])
        
        return APIResponse.success(
            data={'interest_level': interest_level},
            message='Interest level updated successfully'
        )
    
    except Exception as e:
        logger.exception(f"Error updating startup interest: {e}")
        return APIResponse.server_error('Failed to update interest level')


@investor_bp.route('/api/wishlist/<startup_id>', methods=['GET', 'POST'])
@login_required
@investor_required
@handle_api_exception
def wishlist_handler(startup_id):
    """Get or update investor's wishlist for a startup"""
    try:
        user = get_current_user()
        if not user:
            return APIResponse.unauthorized('User not found')
        
        if not firebase_service.db:
            return APIResponse.server_error('Database not available')
        
        # Use a consistent document ID
        wishlist_ref = firebase_service.db.collection('investor_wishlist').document(f"{user['id']}_{startup_id}")
        
        if request.method == 'GET':
            # Get current wishlist status
            doc = wishlist_ref.get()
            if doc.exists:
                data = doc.to_dict()
                return APIResponse.success(data={'wishlisted': data.get('wishlisted', False)})
            else:
                return APIResponse.success(data={'wishlisted': False})
        
        elif request.method == 'POST':
            # Update wishlist status
            data = request.get_json() or {}
            wishlisted = data.get('wishlisted', False)
            
            # Save wishlist data
            wishlist_data = {
                'investor_id': user['id'],
                'startup_id': startup_id,
                'wishlisted': wishlisted,
                'created_at': firestore.SERVER_TIMESTAMP,
                'updated_at': firestore.SERVER_TIMESTAMP
            }
            
            wishlist_ref.set(wishlist_data)
            
            return APIResponse.success(
                data={'wishlisted': wishlisted},
                message='Wishlist updated successfully'
            )
        
    except Exception as e:
        logger.exception(f"Error handling wishlist: {e}")
        return APIResponse.server_error('Failed to handle wishlist')
