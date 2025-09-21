"""
API utilities for AI Investment Platform
Standardized API response formatting and error handling
"""

from flask import jsonify
from typing import Any, Dict, Optional, Union
import logging

logger = logging.getLogger(__name__)


class APIResponse:
    """Standardized API response class"""
    
    @staticmethod
    def success(data: Any = None, message: str = "Success", status_code: int = 200) -> tuple:
        """Create successful API response"""
        response = {
            'success': True,
            'message': message
        }
        
        if data is not None:
            response['data'] = data
        
        return jsonify(response), status_code
    
    @staticmethod
    def error(message: str = "Error", status_code: int = 400, data: Any = None) -> tuple:
        """Create error API response"""
        response = {
            'success': False,
            'message': message
        }
        
        if data is not None:
            response['data'] = data
        
        logger.error(f"API Error {status_code}: {message}")
        return jsonify(response), status_code
    
    @staticmethod
    def validation_error(errors: Dict[str, str], message: str = "Validation failed") -> tuple:
        """Create validation error response"""
        return APIResponse.error(
            message=message,
            status_code=422,
            data={'errors': errors}
        )
    
    @staticmethod
    def unauthorized(message: str = "Authentication required") -> tuple:
        """Create unauthorized response"""
        return APIResponse.error(message=message, status_code=401)
    
    @staticmethod
    def forbidden(message: str = "Access denied") -> tuple:
        """Create forbidden response"""
        return APIResponse.error(message=message, status_code=403)
    
    @staticmethod
    def not_found(message: str = "Resource not found") -> tuple:
        """Create not found response"""
        return APIResponse.error(message=message, status_code=404)
    
    @staticmethod
    def server_error(message: str = "Internal server error") -> tuple:
        """Create server error response"""
        return APIResponse.error(message=message, status_code=500)


def handle_api_exception(func):
    """Decorator to handle API exceptions"""
    from functools import wraps
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            return APIResponse.validation_error({'general': str(e)})
        except PermissionError as e:
            return APIResponse.forbidden(str(e))
        except FileNotFoundError as e:
            return APIResponse.not_found(str(e))
        except Exception as e:
            logger.exception(f"Unexpected error in {func.__name__}: {e}")
            return APIResponse.server_error("An unexpected error occurred")
    
    return wrapper
