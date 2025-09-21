"""
Authentication and authorization utilities for AI Investment Platform
"""

import logging
from functools import wraps
from typing import Any, Dict, Optional
from flask import session, redirect, url_for, flash, request, jsonify
from services.firebase_service import firebase_service

logger = logging.getLogger(__name__)

_PROFILE_SESSION_KEY = 'user_profile'
_PRIMITIVE_TYPES = (str, int, float, bool)


def sanitize_profile_data(data: Any) -> Dict[str, Any]:
    """Return whitelisted profile data that is safe to store in the session."""
    if not isinstance(data, dict):
        return {}

    sanitized: Dict[str, Any] = {}

    for key, value in data.items():
        if value is None:
            continue

        normalized_key = key
        if key in {'photoUrl', 'photo_url'}:
            normalized_key = 'photoURL'

        if normalized_key == 'name' and 'displayName' not in sanitized:
            sanitized['displayName'] = str(value).strip()
            continue

        if normalized_key == 'given_name' and 'firstName' not in sanitized:
            sanitized['firstName'] = str(value).strip()
            continue

        if normalized_key == 'family_name' and 'lastName' not in sanitized:
            sanitized['lastName'] = str(value).strip()
            continue

        if isinstance(value, _PRIMITIVE_TYPES):
            sanitized[normalized_key] = value

    # Ensure displayName is consistently a stripped string where possible.
    if 'displayName' in sanitized and isinstance(sanitized['displayName'], str):
        sanitized['displayName'] = sanitized['displayName'].strip()

    return sanitized


def update_session_profile(data: Any) -> Dict[str, Any]:
    """Merge sanitized profile data into the session and return the result."""
    sanitized = sanitize_profile_data(data)
    if not sanitized:
        return session.get(_PROFILE_SESSION_KEY, {}).copy()

    current_profile = session.get(_PROFILE_SESSION_KEY, {}).copy()
    current_profile.update(sanitized)
    session[_PROFILE_SESSION_KEY] = current_profile
    return current_profile


def _resolve_display_name(profile: Dict[str, Any], email: Optional[str]) -> Optional[str]:
    """Determine the best available display name for the user."""
    display_name = profile.get('displayName') or profile.get('name')
    if isinstance(display_name, str) and display_name.strip():
        return display_name.strip()

    first_name = profile.get('firstName')
    last_name = profile.get('lastName')
    if first_name or last_name:
        return f"{first_name or ''} {last_name or ''}".strip()

    if email:
        return email.split('@')[0]

    return None


def login_required(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json:
                return jsonify({'success': False, 'message': 'Authentication required'}), 401
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def role_required(required_role):
    """Decorator to require specific role"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                if request.is_json:
                    return jsonify({'success': False, 'message': 'Authentication required'}), 401
                return redirect(url_for('auth.login'))
            
            session_role = session.get('user_role')
            firestore_ready = firebase_service.is_firestore_available()
            user_role = firebase_service.get_user_role(session['user_id']) if firestore_ready else session_role

            if not user_role and session_role:
                user_role = session_role

            if not user_role:
                logger.warning(f"User role not found for user {session['user_id']}")
                if request.is_json:
                    return jsonify({'success': False, 'message': 'User role not found'}), 403
                flash('User role not found', 'error')
                return redirect(url_for('auth.login'))
            
            if required_role == 'admin':
                if not firebase_service.is_admin_email(session.get('user_email', '')):
                    logger.warning(f"Access denied for user {session['user_id']} - admin privileges required")
                    if request.is_json:
                        return jsonify({'success': False, 'message': 'Admin privileges required'}), 403
                    flash('Access denied. Admin privileges required.', 'error')
                    return redirect(url_for('home'))
            elif user_role != required_role:
                logger.warning(f"Access denied for user {session['user_id']} - {required_role} role required")
                if request.is_json:
                    return jsonify({'success': False, 'message': f'{required_role.title()} role required'}), 403
                flash(f'Access denied. {required_role.title()} role required.', 'error')
                return redirect(url_for('home'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def admin_required(f):
    """Decorator to require admin privileges"""
    return role_required('admin')(f)


def founder_required(f):
    """Decorator to require founder role"""
    return role_required('founder')(f)


def investor_required(f):
    """Decorator to require investor role"""
    return role_required('investor')(f)


def get_current_user():
    """Get current user data from session and Firestore (when available)."""
    if 'user_id' not in session:
        return None

    profile = session.get(_PROFILE_SESSION_KEY, {}).copy()
    if profile:
        profile = sanitize_profile_data(profile)
        session[_PROFILE_SESSION_KEY] = profile

    if firebase_service.admin_initialized and firebase_service.db:
        firestore_user = firebase_service.get_user_data(session['user_id'])
        if firestore_user:
            profile = update_session_profile({**profile, **firestore_user})
    else:
        # Ensure stored profile data remains sanitized even without Firestore
        if profile:
            profile = update_session_profile(profile)

    email = session.get('user_email')
    display_name = _resolve_display_name(profile, email)
    if display_name:
        profile['displayName'] = display_name

    user = {
        **profile,
        'id': session['user_id'],
        'email': email,
        'role': session.get('user_role')
    }

    # Guarantee these keys exist for template convenience.
    user.setdefault('firstName', profile.get('firstName'))
    user.setdefault('lastName', profile.get('lastName'))
    user.setdefault('photoURL', profile.get('photoURL'))

    name_candidates = [
        user.get('displayName'),
        f"{user.get('firstName') or ''} {user.get('lastName') or ''}".strip(),
        email
    ]
    avatar_label = next((candidate for candidate in name_candidates if isinstance(candidate, str) and candidate.strip()), 'User')
    avatar_label = avatar_label.strip()

    user['avatarLabel'] = avatar_label or 'User'
    user['avatarInitial'] = (user['avatarLabel'][:1].upper() if user['avatarLabel'] else 'U')

    return user


def is_authenticated():
    """Check if user is authenticated"""
    return 'user_id' in session


def logout_user():
    """Logout current user"""
    session.clear()
    logger.info("User logged out successfully")
