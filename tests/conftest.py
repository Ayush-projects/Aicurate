"""
Pytest configuration and fixtures for AI Investment Platform
"""

import pytest
import os
import tempfile
from app_factory import create_app
from config.settings import TestingConfig


@pytest.fixture
def app():
    """Create application for testing"""
    app = create_app('testing')
    app.config.update({
        'TESTING': True,
        'WTF_CSRF_ENABLED': False,
    })
    
    with app.app_context():
        yield app


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create test CLI runner"""
    return app.test_cli_runner()


@pytest.fixture
def auth_headers(client):
    """Get authentication headers for testing"""
    # This would be implemented based on your auth system
    return {
        'Authorization': 'Bearer test-token'
    }
