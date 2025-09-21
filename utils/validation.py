"""
Input validation utilities for AI Investment Platform
"""

import re
from typing import Dict, List, Optional, Any, Union
from email_validator import validate_email, EmailNotValidError


class ValidationError(Exception):
    """Custom validation error"""
    pass


class InputValidator:
    """Input validation class"""
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email address"""
        if not email or not isinstance(email, str):
            return False
        
        try:
            validate_email(email, check_deliverability=False)
            return True
        except EmailNotValidError:
            return False
    
    @staticmethod
    def validate_password(password: str) -> Dict[str, Any]:
        """Validate password strength"""
        if not password or not isinstance(password, str):
            return {'valid': False, 'errors': ['Password is required']}
        
        errors = []
        
        if len(password) < 8:
            errors.append('Password must be at least 8 characters long')
        
        if not re.search(r'[A-Z]', password):
            errors.append('Password must contain at least one uppercase letter')
        
        if not re.search(r'[a-z]', password):
            errors.append('Password must contain at least one lowercase letter')
        
        if not re.search(r'\d', password):
            errors.append('Password must contain at least one number')
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append('Password must contain at least one special character')
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    @staticmethod
    def validate_role(role: str) -> bool:
        """Validate user role"""
        valid_roles = ['founder', 'investor', 'admin']
        return role in valid_roles
    
    @staticmethod
    def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> Dict[str, str]:
        """Validate required fields are present and not empty"""
        errors = {}
        
        for field in required_fields:
            if field not in data or not data[field]:
                errors[field] = f'{field.replace("_", " ").title()} is required'
        
        return errors
    
    @staticmethod
    def validate_string_length(value: str, min_length: int = 0, max_length: int = None) -> bool:
        """Validate string length"""
        if not isinstance(value, str):
            return False
        
        if len(value) < min_length:
            return False
        
        if max_length and len(value) > max_length:
            return False
        
        return True
    
    @staticmethod
    def validate_phone_number(phone: str) -> bool:
        """Validate phone number format"""
        if not phone or not isinstance(phone, str):
            return False
        
        # Remove all non-digit characters
        digits_only = re.sub(r'\D', '', phone)
        
        # Check if it's a valid length (10-15 digits)
        return 10 <= len(digits_only) <= 15
    
    @staticmethod
    def validate_company_name(name: str) -> bool:
        """Validate company name"""
        if not name or not isinstance(name, str):
            return False
        
        # Company name should be 2-100 characters, alphanumeric and spaces
        if not re.match(r'^[a-zA-Z0-9\s\-&.,()]{2,100}$', name):
            return False
        
        return True
    
    @staticmethod
    def validate_funding_amount(amount: Union[str, int, float]) -> bool:
        """Validate funding amount"""
        try:
            amount_float = float(amount)
            return amount_float > 0 and amount_float <= 1000000000  # Max 1 billion
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def sanitize_input(value: str) -> str:
        """Sanitize input string"""
        if not isinstance(value, str):
            return str(value)
        
        # Remove potentially dangerous characters
        sanitized = re.sub(r'[<>"\']', '', value)
        return sanitized.strip()
    
    @staticmethod
    def validate_file_type(filename: str, allowed_extensions: List[str]) -> bool:
        """Validate file type based on extension"""
        if not filename or not isinstance(filename, str):
            return False
        
        file_extension = filename.lower().split('.')[-1] if '.' in filename else ''
        return file_extension in [ext.lower() for ext in allowed_extensions]
    
    @staticmethod
    def validate_file_size(file_size: int, max_size_mb: int = 50) -> bool:
        """Validate file size"""
        max_size_bytes = max_size_mb * 1024 * 1024
        return 0 < file_size <= max_size_bytes
    
    @staticmethod
    def validate_startup_submission(data: Dict[str, Any]) -> Dict[str, str]:
        """Validate startup submission data"""
        errors = {}
        
        # Required fields
        required_fields = ['startupName', 'description', 'location', 'foundingDate']
        errors.update(InputValidator.validate_required_fields(data, required_fields))
        
        # Validate startup name
        if 'startupName' in data and not InputValidator.validate_company_name(data['startupName']):
            errors['startupName'] = 'Invalid startup name format'
        
        # Validate description (only check if it's not empty)
        if 'description' in data and not data['description'].strip():
            errors['description'] = 'Description is required'
        
        # Validate location
        if 'location' in data:
            location = data['location']
            if not isinstance(location, dict):
                errors['location'] = 'Location must be an object'
            else:
                location_required = ['city', 'state', 'country']
                for field in location_required:
                    if field not in location or not location[field]:
                        errors[f'location.{field}'] = f'{field.title()} is required'
        
        # Validate founding date
        if 'foundingDate' in data:
            try:
                from datetime import datetime
                datetime.fromisoformat(data['foundingDate'].replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                errors['foundingDate'] = 'Invalid founding date format'
        
        return errors


def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> Dict[str, str]:
    """Validate required fields are present and not empty"""
    return InputValidator.validate_required_fields(data, required_fields)


def validate_login_data(data: Dict[str, Any]) -> Dict[str, str]:
    """Validate login form data"""
    errors = {}
    
    # Check required fields
    required_fields = ['email', 'password']
    errors.update(InputValidator.validate_required_fields(data, required_fields))
    
    # Validate email
    if 'email' in data and not InputValidator.validate_email(data['email']):
        errors['email'] = 'Invalid email format'
    
    return errors


def validate_signup_data(data: Dict[str, Any]) -> Dict[str, str]:
    """Validate signup form data"""
    errors = {}
    
    # Check required fields
    required_fields = ['email', 'password', 'role']
    errors.update(InputValidator.validate_required_fields(data, required_fields))
    
    # Validate email
    if 'email' in data and not InputValidator.validate_email(data['email']):
        errors['email'] = 'Invalid email format'
    
    # Validate password
    if 'password' in data:
        password_validation = InputValidator.validate_password(data['password'])
        if not password_validation['valid']:
            errors['password'] = '; '.join(password_validation['errors'])
    
    # Validate role
    if 'role' in data and not InputValidator.validate_role(data['role']):
        errors['role'] = 'Invalid role selected'
    
    return errors