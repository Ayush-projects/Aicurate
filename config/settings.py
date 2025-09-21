"""
Configuration settings for AI Investment Platform
Centralized configuration management with environment variable support
"""

import os
from typing import List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Base configuration class"""
    
    # Flask Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    DEBUG = os.getenv('FLASK_ENV') == 'development'
    
    # Server Configuration
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 5000))
    
    # Admin Configuration
    ADMIN_EMAILS = os.getenv('ADMIN_EMAILS', 'admin@company.com').split(',')
    
    # Firebase Configuration (Client-side)
    FIREBASE_API_KEY = os.getenv('FIREBASE_API_KEY')
    FIREBASE_AUTH_DOMAIN = os.getenv('FIREBASE_AUTH_DOMAIN')
    FIREBASE_PROJECT_ID = os.getenv('FIREBASE_PROJECT_ID')
    FIREBASE_STORAGE_BUCKET = os.getenv('FIREBASE_STORAGE_BUCKET')
    FIREBASE_MESSAGING_SENDER_ID = os.getenv('FIREBASE_MESSAGING_SENDER_ID')
    FIREBASE_APP_ID = os.getenv('FIREBASE_APP_ID')
    
    # Firebase Admin SDK Configuration (Server-side)
    FIREBASE_PRIVATE_KEY = os.getenv('FIREBASE_PRIVATE_KEY')
    FIREBASE_CLIENT_EMAIL = os.getenv('FIREBASE_CLIENT_EMAIL')
    FIREBASE_PRIVATE_KEY_ID = os.getenv('FIREBASE_PRIVATE_KEY_ID')
    FIREBASE_CLIENT_ID = os.getenv('FIREBASE_CLIENT_ID')
    
    # Security Configuration
    SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'app.log')
    
    # File Upload Configuration
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 500 * 1024 * 1024))  # 500MB max file size
    
    @classmethod
    def get_firebase_config(cls) -> dict:
        """Get Firebase configuration for client-side"""
        return {
            "apiKey": cls.FIREBASE_API_KEY,
            "authDomain": cls.FIREBASE_AUTH_DOMAIN,
            "projectId": cls.FIREBASE_PROJECT_ID,
            "storageBucket": cls.FIREBASE_STORAGE_BUCKET,
            "messagingSenderId": cls.FIREBASE_MESSAGING_SENDER_ID,
            "appId": cls.FIREBASE_APP_ID
        }
    
    @classmethod
    def get_pyrebase_config(cls) -> dict:
        """Get Pyrebase configuration"""
        return {
            "apiKey": cls.FIREBASE_API_KEY,
            "authDomain": cls.FIREBASE_AUTH_DOMAIN,
            "projectId": cls.FIREBASE_PROJECT_ID,
            "storageBucket": cls.FIREBASE_STORAGE_BUCKET,
            "messagingSenderId": cls.FIREBASE_MESSAGING_SENDER_ID,
            "appId": cls.FIREBASE_APP_ID,
            "databaseURL": ""
        }
    
    @classmethod
    def validate_config(cls) -> List[str]:
        """Validate configuration and return list of missing required fields"""
        missing_fields = []
        
        # Required fields for client-side Firebase
        required_fields = [
            'FIREBASE_API_KEY',
            'FIREBASE_AUTH_DOMAIN', 
            'FIREBASE_PROJECT_ID',
            'FIREBASE_STORAGE_BUCKET',
            'FIREBASE_MESSAGING_SENDER_ID',
            'FIREBASE_APP_ID'
        ]
        
        for field in required_fields:
            if not getattr(cls, field):
                missing_fields.append(field)
        
        return missing_fields
    
    @classmethod
    def validate_admin_config(cls) -> List[str]:
        """Validate Firebase Admin SDK configuration (optional)"""
        missing_fields = []
        
        # Check if we have environment variables for Admin SDK
        admin_required_fields = [
            'FIREBASE_PRIVATE_KEY',
            'FIREBASE_CLIENT_EMAIL'
        ]
        
        for field in admin_required_fields:
            if not getattr(cls, field):
                missing_fields.append(field)
        
        return missing_fields


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True


# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
