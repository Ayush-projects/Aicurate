"""
Application factory for AI Investment Platform
Creates and configures the Flask application
"""

from flask import Flask
from config.settings import config
from utils.logging_config import setup_logging
from services.firebase_service import firebase_service
import logging

logger = logging.getLogger(__name__)


def create_app(config_name='default'):
    """Create and configure Flask application"""
    
    # Create Flask app
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Configure file upload settings
    app.config['MAX_CONTENT_LENGTH'] = config[config_name].MAX_CONTENT_LENGTH
    
    # Setup logging
    setup_logging()
    
    # Initialize Firebase service
    if not firebase_service.admin_initialized:
        logger.warning("Firebase Admin SDK not initialized - some features may not work")
    
    # Register blueprints
    from blueprints.auth import auth_bp
    from blueprints.founder import founder_bp
    from blueprints.investor import investor_bp
    from blueprints.admin import admin_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(founder_bp, url_prefix='/founder')
    app.register_blueprint(investor_bp, url_prefix='/investor')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    # Register main routes
    register_main_routes(app)
    
    # Register static file routes for uploads
    register_static_routes(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    logger.info("Flask application created successfully")
    return app


def register_main_routes(app):
    """Register main application routes"""
    
    @app.route('/')
    def home():
        """Homepage with role selection or redirect to dashboard if logged in"""
        from flask import render_template, redirect, url_for
        from config.settings import Config
        from utils.auth import get_current_user
        
        # Check if user is already logged in
        user = get_current_user()
        if user:
            # Redirect to appropriate dashboard based on role
            role = user.get('role')
            if role == 'founder':
                return redirect(url_for('founder.dashboard'))
            elif role == 'investor':
                return redirect(url_for('investor.dashboard'))
            elif role == 'admin':
                return redirect(url_for('admin.dashboard'))
            else:
                # If role is invalid, redirect to dashboard route for handling
                return redirect(url_for('dashboard'))
        
        # User not logged in, show home page
        return render_template('home.html', firebase_config=Config.get_firebase_config())
    
    @app.route('/dashboard')
    def dashboard():
        """Redirect to role-based dashboard"""
        from flask import session, redirect, url_for, flash
        from utils.auth import get_current_user
        
        user = get_current_user()
        if not user:
            flash('User data not found', 'error')
            return redirect(url_for('auth.login'))
        
        role = user.get('role')
        if role == 'founder':
            return redirect(url_for('founder.dashboard'))
        elif role == 'investor':
            return redirect(url_for('investor.dashboard'))
        elif role == 'admin':
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Invalid user role', 'error')
            return redirect(url_for('auth.login'))


def register_static_routes(app):
    """Register static file routes for uploads"""
    
    @app.route('/uploads/<path:filename>')
    def uploaded_file(filename):
        """Serve uploaded files"""
        from flask import send_from_directory, abort
        import os
        
        upload_folder = app.config.get('UPLOAD_FOLDER', 'uploads')
        file_path = os.path.join(upload_folder, filename)
        
        if os.path.exists(file_path):
            return send_from_directory(upload_folder, filename)
        else:
            abort(404)


def register_error_handlers(app):
    """Register error handlers"""
    
    @app.errorhandler(404)
    def not_found_error(error):
        from flask import render_template
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        from flask import render_template
        logger.exception("Internal server error")
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(403)
    def forbidden_error(error):
        from flask import render_template
        return render_template('errors/403.html'), 403
