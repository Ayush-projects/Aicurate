"""
AI Investment Platform - Main Application
This file creates the Flask application using the application factory pattern
"""

from app_factory import create_app
from config.settings import Config
import logging

# Create the Flask application
app = create_app()

# Validate configuration
missing_config = Config.validate_config()
if missing_config:
    logging.error(f"Missing required configuration: {', '.join(missing_config)}")
    logging.error("Application cannot start without required configuration")
    exit(1)

# Check Firebase Admin SDK configuration (optional)
missing_admin_config = Config.validate_admin_config()
if missing_admin_config:
    logging.warning(f"Firebase Admin SDK configuration missing: {', '.join(missing_admin_config)}")
    logging.warning("Some features may not work without Firebase Admin SDK")

if __name__ == '__main__':
    app.run(debug=Config.DEBUG, host=Config.HOST, port=Config.PORT)
