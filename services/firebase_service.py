"""
Firebase service for AI Investment Platform
Handles all Firebase operations using SDK with environment variables
"""

import logging
from typing import Optional, Dict, Any

import firebase_admin
from firebase_admin import credentials, firestore, auth as firebase_auth_admin
import requests

from config.settings import Config

logger = logging.getLogger(__name__)


class FirebaseService:
    """Service class for Firebase operations"""
    
    def __init__(self):
        self.db = None
        self.admin_initialized = False
        self.api_key = Config.FIREBASE_API_KEY
        self._initialize_firebase()
    
    def _initialize_firebase(self):
        """Initialize Firebase Admin SDK and Pyrebase using environment variables"""
        try:
            # Initialize Firebase Admin SDK with environment variables
            if all([
                Config.FIREBASE_PROJECT_ID,
                Config.FIREBASE_PRIVATE_KEY,
                Config.FIREBASE_CLIENT_EMAIL
            ]):
                # Create credentials from environment variables
                cred_dict = {
                    "type": "service_account",
                    "project_id": Config.FIREBASE_PROJECT_ID,
                    "private_key_id": Config.FIREBASE_PRIVATE_KEY_ID or "",
                    "private_key": Config.FIREBASE_PRIVATE_KEY.replace('\\n', '\n'),
                    "client_email": Config.FIREBASE_CLIENT_EMAIL,
                    "client_id": Config.FIREBASE_CLIENT_ID or "",
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                    "client_x509_cert_url": f"https://www.googleapis.com/robot/v1/metadata/x509/{Config.FIREBASE_CLIENT_EMAIL}"
                }
                
                cred = credentials.Certificate(cred_dict)

                if firebase_admin._apps:
                    firebase_admin.get_app()
                else:
                    firebase_admin.initialize_app(cred)

                self.db = firestore.client()
                self.admin_initialized = True
                logger.info("Firebase Admin SDK initialized with environment variables")
            else:
                logger.warning("Firebase Admin SDK environment variables not found")
                self.admin_initialized = False
        except Exception as e:
            logger.error(f"Firebase Admin initialization failed: {e}")
            self.admin_initialized = False

    def is_firestore_available(self) -> bool:
        """Return True when the Firestore client is ready for use."""
        if not self.admin_initialized or not self.db:
            return False

        try:
            # Trigger a lightweight call to ensure the client is usable.
            iterator = iter(self.db.collections())
            next(iterator, None)
            return True
        except Exception as exc:
            logger.warning("Firestore connectivity check failed: %s", exc)
            return False

    def get_user_role(self, uid: str) -> Optional[str]:
        """Get user role from Firestore"""
        if not self.admin_initialized or not self.db:
            logger.warning("Firebase Admin not initialized, cannot get user role")
            return None
        
        try:
            user_doc = self.db.collection('users').document(uid).get()
            if user_doc.exists:
                return user_doc.to_dict().get('role')
            return None
        except Exception as e:
            logger.warning(f"Error getting user role: {e}")
            return None
    
    def get_user_data(self, uid: str) -> Optional[Dict[str, Any]]:
        """Get complete user data from Firestore"""
        if not self.admin_initialized or not self.db:
            logger.warning("Firebase Admin not initialized, cannot get user data")
            return None
        
        try:
            user_doc = self.db.collection('users').document(uid).get()
            if user_doc.exists:
                return user_doc.to_dict()
            return None
        except Exception as e:
            logger.warning(f"Error getting user data: {e}")
            return None
    
    def create_user_profile(self, uid: str, email: str, role: str, additional_data: Optional[Dict[str, Any]] = None) -> bool:
        """Create user profile in Firestore"""
        if not self.admin_initialized or not self.db:
            logger.warning("Firebase Admin not initialized, cannot create user profile")
            return False
        
        try:
            user_data = {
                'email': email,
                'role': role,
                'created_at': firestore.SERVER_TIMESTAMP,
                'profile_complete': False,
                'active': True
            }
            
            if additional_data:
                user_data.update(additional_data)
            
            self.db.collection('users').document(uid).set(user_data)
            logger.info(f"User profile created successfully for {email}")
            return True
        except Exception as e:
            logger.warning(f"Error creating user profile: {e}")
            return False
    
    def update_user_profile(self, uid: str, update_data: Dict[str, Any]) -> bool:
        """Update user profile in Firestore"""
        if not self.admin_initialized or not self.db:
            logger.warning("Firebase Admin not initialized, cannot update user profile")
            return False
        
        try:
            update_data['updated_at'] = firestore.SERVER_TIMESTAMP
            self.db.collection('users').document(uid).update(update_data)
            logger.info(f"User profile updated successfully for {uid}")
            return True
        except Exception as e:
            logger.warning(f"Error updating user profile: {e}")
            return False
    
    def verify_id_token(self, id_token: str) -> Optional[Dict[str, Any]]:
        """Verify Firebase ID token"""
        if not self.admin_initialized:
            logger.warning("Firebase Admin not initialized, cannot verify token")
            return None
        
        try:
            decoded_token = firebase_auth_admin.verify_id_token(id_token)
            logger.debug(f"Token verification successful for UID: {decoded_token.get('uid', 'unknown')}")
            return decoded_token
        except Exception as e:
            logger.error(f"Error verifying ID token: {e}")
            logger.error(f"Token preview: {id_token[:50] if id_token else 'None'}...")
            return None
    
    def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user with email and password using Firebase REST API"""
        if not self.api_key:
            logger.error("Firebase API key not configured, cannot authenticate user")
            return None
        
        try:
            response = requests.post(
                "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword",
                params={"key": self.api_key},
                json={
                    "email": email,
                    "password": password,
                    "returnSecureToken": True
                },
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            return {
                'uid': data.get('localId'),
                'email': data.get('email', email),
                'id_token': data.get('idToken'),
                'refresh_token': data.get('refreshToken'),
                'display_name': data.get('displayName'),
                'photo_url': data.get('photoUrl')
            }
        except requests.exceptions.HTTPError as http_err:
            logger.warning(f"Firebase authentication failed for {email}: {http_err}")
            return None
        except requests.RequestException as req_err:
            logger.error(f"Error communicating with Firebase Auth REST API: {req_err}")
            return None
    
    def create_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Create new user with email and password"""
        if not self.admin_initialized:
            logger.error("Firebase Admin not initialized, cannot create user")
            return None
        
        try:
            user_record = firebase_auth_admin.create_user(email=email, password=password)
            return {
                'uid': user_record.uid,
                'email': user_record.email
            }
        except firebase_auth_admin.EmailAlreadyExistsError:
            logger.warning(f"User with email {email} already exists")
            return None
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return None
    
    def is_admin_email(self, email: str) -> bool:
        """Check if email is in admin whitelist"""
        return email in Config.ADMIN_EMAILS


# Global Firebase service instance
firebase_service = FirebaseService()
