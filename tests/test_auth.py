"""
Tests for authentication functionality
"""

import pytest
from utils.validation import validate_login_data, validate_signup_data, InputValidator


class TestInputValidation:
    """Test input validation functions"""
    
    def test_validate_email(self):
        """Test email validation"""
        assert InputValidator.validate_email('test@example.com') == True
        assert InputValidator.validate_email('invalid-email') == False
        assert InputValidator.validate_email('') == False
        assert InputValidator.validate_email(None) == False
    
    def test_validate_password(self):
        """Test password validation"""
        # Valid password
        result = InputValidator.validate_password('Password123!')
        assert result['valid'] == True
        assert len(result['errors']) == 0
        
        # Weak password
        result = InputValidator.validate_password('123')
        assert result['valid'] == False
        assert len(result['errors']) > 0
    
    def test_validate_role(self):
        """Test role validation"""
        assert InputValidator.validate_role('founder') == True
        assert InputValidator.validate_role('investor') == True
        assert InputValidator.validate_role('admin') == True
        assert InputValidator.validate_role('invalid') == False
    
    def test_validate_login_data(self):
        """Test login data validation"""
        # Valid data
        data = {'email': 'test@example.com', 'password': 'password123'}
        errors = validate_login_data(data)
        assert len(errors) == 0
        
        # Missing email
        data = {'password': 'password123'}
        errors = validate_login_data(data)
        assert 'email' in errors
        
        # Invalid email
        data = {'email': 'invalid-email', 'password': 'password123'}
        errors = validate_login_data(data)
        assert 'email' in errors
    
    def test_validate_signup_data(self):
        """Test signup data validation"""
        # Valid data
        data = {
            'email': 'test@example.com',
            'password': 'Password123!',
            'role': 'founder'
        }
        errors = validate_signup_data(data)
        assert len(errors) == 0
        
        # Missing fields
        data = {'email': 'test@example.com'}
        errors = validate_signup_data(data)
        assert 'password' in errors
        assert 'role' in errors
        
        # Invalid role
        data = {
            'email': 'test@example.com',
            'password': 'Password123!',
            'role': 'invalid'
        }
        errors = validate_signup_data(data)
        assert 'role' in errors
