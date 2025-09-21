from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from config.settings import Config
from services.firebase_service import firebase_service
from utils.api import APIResponse, handle_api_exception
from utils.validation import validate_login_data, validate_signup_data
from utils.auth import logout_user, update_session_profile
import logging

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login')
def login():
    """Login page"""
    return render_template(
        'auth/login.html',
        firebase_config=Config.get_firebase_config()
    )

@auth_bp.route('/signup')
def signup():
    """Signup page"""
    return render_template(
        'auth/signup.html',
        firebase_config=Config.get_firebase_config(),
        selected_role=None
    )

@auth_bp.route('/signup/<role>')
def signup_role(role):
    """Signup page for specific role"""
    if role not in ['founder', 'investor']:
        flash('Invalid role selected', 'error')
        return redirect(url_for('auth.signup'))
    return render_template(
        'auth/signup.html',
        firebase_config=Config.get_firebase_config(),
        selected_role=role
    )

@auth_bp.route('/api/login', methods=['POST'])
@handle_api_exception
def api_login():
    """API endpoint for login"""
    data = request.get_json()
    
    # Validate input
    validation_errors = validate_login_data(data)
    if validation_errors:
        return APIResponse.validation_error(validation_errors)
    
    email = data['email']
    password = data['password']
    
    # Authenticate with Firebase
    auth_result = firebase_service.authenticate_user(email, password)
    if not auth_result:
        return APIResponse.error('Invalid email or password', 401)

    uid = auth_result['uid']
    
    # Get user role from Firestore
    firestore_ready = firebase_service.admin_initialized and firebase_service.db
    role = firebase_service.get_user_role(uid) if firestore_ready else None
    if not role:
        # If user doesn't exist in Firestore (or Firestore is unavailable), fallback to default role
        role = 'founder'
        if firestore_ready:
            firebase_service.create_user_profile(uid, email, role)
            logger.info(f"Created default profile for user {email}")
    
    # Reset any lingering profile data before creating the new session
    session.pop('user_profile', None)

    # Store in session
    session['user_id'] = uid
    session['user_email'] = email
    session['user_role'] = role
    session['id_token'] = auth_result['id_token']

    profile_payload = {}

    if firestore_ready:
        firestore_profile = firebase_service.get_user_data(uid)
        if firestore_profile:
            profile_payload.update(firestore_profile)

    if auth_result.get('display_name'):
        profile_payload.setdefault('displayName', auth_result['display_name'])

    if auth_result.get('photo_url'):
        profile_payload['photoURL'] = auth_result['photo_url']

    if not profile_payload.get('displayName'):
        profile_payload['displayName'] = email.split('@')[0]

    update_session_profile(profile_payload)

    logger.info(f"User logged in: {email} with role {role}")
    return APIResponse.success(
        data={'role': role, 'redirect_url': '/dashboard'},
        message='Login successful'
    )

@auth_bp.route('/api/signup', methods=['POST'])
@handle_api_exception
def api_signup():
    """API endpoint for signup"""
    data = request.get_json() or {}

    role = data.get('role')
    id_token = data.get('idToken')

    if role not in ['founder', 'investor']:
        return APIResponse.error('Valid role is required', 400)

    # Frontend-managed signup (Firebase client returns ID token)
    decoded_token = None
    if id_token:
        logger.info(f"Attempting to verify ID token for signup. Token length: {len(id_token) if id_token else 0}")
        decoded_token = firebase_service.verify_id_token(id_token)
        if not decoded_token:
            logger.error(f"Token verification failed for signup. Token preview: {id_token[:50] if id_token else 'None'}...")
            # Fall back to server-managed signup if token verification fails
            logger.info("Falling back to server-managed signup due to token verification failure")
            id_token = None  # This will trigger the server-managed signup flow below
        else:
            logger.info(f"Token verification successful for user: {decoded_token.get('uid', 'unknown')}")

    if id_token and decoded_token:
        uid = decoded_token['uid']
        email = decoded_token.get('email') or data.get('email')

        if not email:
            return APIResponse.error('Email is required to complete signup', 400)

        first_name = (data.get('firstName') or decoded_token.get('given_name') or '').strip()
        last_name = (data.get('lastName') or decoded_token.get('family_name') or '').strip()
        display_name_claim = data.get('displayName') or decoded_token.get('name')
        photo_url = (data.get('photoURL') or decoded_token.get('picture') or '').strip()
        provider = decoded_token.get('firebase', {}).get('sign_in_provider', 'password')

        firestore_ready = firebase_service.admin_initialized and firebase_service.db
        existing_role = firebase_service.get_user_role(uid) if firestore_ready else None
        created_profile = False

        if not existing_role and firestore_ready:
            profile_display_name = display_name_claim.strip() if isinstance(display_name_claim, str) and display_name_claim.strip() else None
            if not profile_display_name:
                profile_display_name = f"{first_name} {last_name}".strip() or email.split('@')[0]

            additional_data = {
                'auth_provider': provider,
                'signup_method': provider,
                'displayName': profile_display_name,
                'profile_complete': bool(first_name and last_name)
            }

            if first_name:
                additional_data['firstName'] = first_name
            if last_name:
                additional_data['lastName'] = last_name
            if photo_url:
                additional_data['photoURL'] = photo_url

            created_profile = firebase_service.create_user_profile(
                uid,
                email,
                role,
                additional_data=additional_data
            )

            if not created_profile:
                logger.warning(
                    "Firestore profile creation skipped for %s; continuing with session-only role storage",
                    email
                )
            else:
                existing_role = role

        if not existing_role:
            existing_role = role

        # Store in session
        session.pop('user_profile', None)
        session['user_id'] = uid
        session['user_email'] = email
        session['user_role'] = existing_role
        session['id_token'] = id_token

        computed_display_name = (
            display_name_claim.strip() if isinstance(display_name_claim, str) and display_name_claim.strip()
            else f"{first_name} {last_name}".strip() or email.split('@')[0]
        )

        profile_payload = {
            'displayName': computed_display_name,
            'profile_complete': bool(first_name and last_name)
        }

        if first_name:
            profile_payload['firstName'] = first_name
        if last_name:
            profile_payload['lastName'] = last_name
        if photo_url:
            profile_payload['photoURL'] = photo_url

        update_session_profile(profile_payload)

        if created_profile and firestore_ready:
            firestore_profile = firebase_service.get_user_data(uid)
            if firestore_profile:
                update_session_profile(firestore_profile)

        logger.info(f"User signed up via client auth: {email} with role {existing_role}")
        message = 'Account created successfully' if created_profile else 'Account verified successfully'
        return APIResponse.success(
            data={'role': existing_role, 'redirect_url': '/investor/preferences' if existing_role == 'investor' else '/dashboard'},
            message=message
        )

    # Server-managed signup fallback (email/password provided to backend)
    logger.info("Using server-managed signup flow")
    validation_errors = validate_signup_data(data)
    if validation_errors:
        return APIResponse.validation_error(validation_errors)

    email = data['email']
    password = data['password']

    auth_result = firebase_service.create_user(email, password)
    if not auth_result:
        return APIResponse.error('Failed to create user account', 400)

    uid = auth_result['uid']

    # Sign the user in to obtain tokens for the session
    login_result = firebase_service.authenticate_user(email, password)
    if not login_result:
        logger.error("User created but failed to authenticate for session establishment")
        return APIResponse.error('Account created but failed to start session. Please log in manually.', 500)

    firestore_ready = firebase_service.admin_initialized and firebase_service.db
    created_profile = False
    if firestore_ready:
        created_profile = firebase_service.create_user_profile(uid, email, role)
        if not created_profile:
            logger.warning(f"Failed to create user profile for {email}, but user exists in Firebase Auth")
    else:
        logger.info("Skipping Firestore profile creation for %s; Firestore is unavailable", email)

    session.pop('user_profile', None)
    session['user_id'] = uid
    session['user_email'] = email
    session['user_role'] = role
    session['id_token'] = login_result['id_token']

    profile_payload = {
        'displayName': (data.get('displayName') or '').strip() or email.split('@')[0]
    }

    if data.get('firstName'):
        profile_payload['firstName'] = data['firstName'].strip()
    if data.get('lastName'):
        profile_payload['lastName'] = data['lastName'].strip()
    if data.get('photoURL'):
        profile_payload['photoURL'] = data['photoURL'].strip()

    update_session_profile(profile_payload)

    if created_profile and firestore_ready:
        firestore_profile = firebase_service.get_user_data(uid)
        if firestore_profile:
            update_session_profile(firestore_profile)

    logger.info(f"User signed up via backend: {email} with role {role}")
    return APIResponse.success(
        data={'role': role, 'redirect_url': '/investor/preferences' if role == 'investor' else '/dashboard'},
        message='Account created successfully'
    )

@auth_bp.route('/logout')
def logout():
    """Logout user"""
    logout_user()
    flash('You have been logged out successfully', 'success')
    return redirect(url_for('home'))

@auth_bp.route('/api/verify-token', methods=['POST'])
@handle_api_exception
def verify_token():
    """Verify Firebase ID token"""
    data = request.get_json()
    id_token = data.get('idToken')
    requested_role = data.get('role')

    if not id_token:
        return APIResponse.error('Token required', 400)

    if requested_role not in ['founder', 'investor', None]:
        logger.warning("Invalid role provided during token verification")
        requested_role = None
    
    # Verify token with Firebase Admin
    decoded_token = firebase_service.verify_id_token(id_token)
    if not decoded_token:
        return APIResponse.error('Invalid token', 401)
    
    uid = decoded_token['uid']
    email = decoded_token.get('email', '')
    first_name = (data.get('firstName') or decoded_token.get('given_name') or '').strip()
    last_name = (data.get('lastName') or decoded_token.get('family_name') or '').strip()
    display_name_claim = data.get('displayName') or decoded_token.get('name')
    photo_url = (data.get('photoURL') or decoded_token.get('picture') or '').strip()
    provider = decoded_token.get('firebase', {}).get('sign_in_provider', 'google')
    firestore_ready = firebase_service.admin_initialized and firebase_service.db

    # Get user role
    role = firebase_service.get_user_role(uid) if firestore_ready else None
    if not role:
        fallback_role = requested_role or 'founder'
        profile_display_name = display_name_claim.strip() if isinstance(display_name_claim, str) and display_name_claim.strip() else None
        if not profile_display_name:
            profile_display_name = f"{first_name} {last_name}".strip() or email.split('@')[0]

        additional_data = {
            'auth_provider': provider,
            'signup_method': 'google_oauth',
            'displayName': profile_display_name,
            'profile_complete': bool(first_name and last_name)
        }

        if first_name:
            additional_data['firstName'] = first_name
        if last_name:
            additional_data['lastName'] = last_name
        if photo_url:
            additional_data['photoURL'] = photo_url

        created = False
        if firestore_ready:
            created = firebase_service.create_user_profile(
                uid,
                email,
                fallback_role,
                additional_data=additional_data
            )

        if not created:
            log_fn = logger.warning if firestore_ready else logger.info
            log_fn(
                "Firestore profile creation skipped for Google sign-in %s; defaulting role to %s",
                email,
                fallback_role
            )
            role = fallback_role
        else:
            role = fallback_role
            logger.info(f"Created new profile for {email} via Google sign-in with role {role}")

    # Update session
    session.pop('user_profile', None)
    session['user_id'] = uid
    session['user_email'] = email
    session['user_role'] = role
    session['id_token'] = id_token

    computed_display_name = (
        display_name_claim.strip() if isinstance(display_name_claim, str) and display_name_claim.strip()
        else f"{first_name} {last_name}".strip() or (email.split('@')[0] if email else None)
    )

    profile_payload = {}
    if computed_display_name:
        profile_payload['displayName'] = computed_display_name
    if first_name:
        profile_payload['firstName'] = first_name
    if last_name:
        profile_payload['lastName'] = last_name
    if photo_url:
        profile_payload['photoURL'] = photo_url
    profile_payload['profile_complete'] = bool(first_name and last_name)

    update_session_profile(profile_payload)

    if firestore_ready:
        firestore_profile = firebase_service.get_user_data(uid)
        if firestore_profile:
            update_session_profile(firestore_profile)
    
    logger.info(f"Token verified for user {uid}")
    return APIResponse.success(
        data={'role': role, 'redirect_url': '/dashboard'},
        message='Token verified successfully'
    )
