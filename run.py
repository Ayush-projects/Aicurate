#!/usr/bin/env python3
"""
AI Investment Platform - Startup Script
Run this script to start the development server
"""

import os
import sys
import logging
from app import app
from config.settings import Config

def check_environment():
    """Check environment setup and configuration"""
    warnings = []
    errors = []
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        warnings.append("Warning: .env file not found!")
        warnings.append("Please copy env_example.txt to .env and configure your Firebase credentials")
        warnings.append("cp env_example.txt .env")
    
    # Check Firebase Admin SDK credentials (optional)
    missing_admin_config = Config.validate_admin_config()
    if missing_admin_config:
        warnings.append("Warning: Firebase Admin SDK credentials not found!")
        warnings.append("Please set FIREBASE_PRIVATE_KEY and FIREBASE_CLIENT_EMAIL in .env")
        warnings.append("You can get these values from your Firebase service account JSON file")
        warnings.append("Download from: https://console.firebase.google.com/project/YOUR_PROJECT/settings/serviceaccounts/adminsdk")
        warnings.append("Note: Some features may not work without Admin SDK credentials")
    
    # Check required configuration
    missing_config = Config.validate_config()
    if missing_config:
        errors.append("Missing required configuration:")
        for field in missing_config:
            errors.append(f"   - {field}")
        errors.append("Please check your .env file and ensure all Firebase credentials are set")
    
    return warnings, errors

def main():
    """Main function to start the application"""
    print("Starting AI Investment Platform...")
    print("=" * 50)
    
    # Check environment
    warnings, errors = check_environment()
    
    # Print warnings
    if warnings:
        print("\n".join(warnings))
        print()
    
    # Print errors and exit if any
    if errors:
        print("\n".join(errors))
        print("\nCannot start server due to configuration errors")
        sys.exit(1)
    
    # Print startup information
    print(f"Server will be available at: http://{Config.HOST}:{Config.PORT}")
    print(f"Environment: {Config.FLASK_ENV}")
    print(f"Debug mode: {'ON' if Config.DEBUG else 'OFF'}")
    print(f"Log level: {Config.LOG_LEVEL}")
    print("Press Ctrl+C to stop the server")
    print("=" * 50)
    
    try:
        app.run(debug=Config.DEBUG, host=Config.HOST, port=Config.PORT)
    except KeyboardInterrupt:
        print("Server stopped. Goodbye!")
    except Exception as e:
        logging.exception("Error starting server")
        print(f"Error starting server: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
