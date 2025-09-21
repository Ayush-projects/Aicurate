"""
File upload service for AI Investment Platform
Handles file uploads, storage, and management
"""

import os
import uuid
import logging
from typing import Dict, Any, Optional, List
from werkzeug.utils import secure_filename
from flask import current_app
import mimetypes

logger = logging.getLogger(__name__)


class FileUploadService:
    """Service class for handling file uploads"""
    
    # Allowed file types for different categories
    ALLOWED_EXTENSIONS = {
        'pitch_deck': ['pdf', 'ppt', 'pptx'],
        'video_pitch': ['mp4', 'avi', 'mov', 'wmv', 'webm'],
        'audio_pitch': ['mp3', 'wav', 'm4a', 'aac'],
        'financial_model': ['xlsx', 'xls', 'csv'],
        'product_demo': ['mp4', 'avi', 'mov', 'wmv', 'webm'],
        'founder_update': ['docx', 'doc', 'pdf', 'txt', 'ppt', 'pptx'],
        'supporting_document': ['pdf', 'doc', 'docx', 'txt', 'rtf', 'xlsx', 'xls', 'csv', 'ppt', 'pptx'],
        'image': ['jpg', 'jpeg', 'png', 'gif', 'webp'],
        'document': ['pdf', 'doc', 'docx', 'txt', 'rtf', 'ppt', 'pptx']
    }
    
    # File size limits in MB
    MAX_FILE_SIZES = {
        'pitch_deck': 50,
        'video_pitch': 500,
        'audio_pitch': 100,
        'financial_model': 10,
        'product_demo': 500,
        'founder_update': 20,
        'supporting_document': 25,
        'image': 10,
        'document': 20
    }
    
    def __init__(self):
        self.upload_folder = None
        self._directories_ensured = False
    
    def _ensure_upload_directories(self):
        """Create upload directories if they don't exist"""
        if self._directories_ensured:
            return
            
        # Initialize upload folder if not set
        if not self.upload_folder:
            try:
                self.upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
            except RuntimeError:
                # Fallback if not in app context
                self.upload_folder = 'uploads'
        
        directories = [
            self.upload_folder,
            os.path.join(self.upload_folder, 'pitch_decks'),
            os.path.join(self.upload_folder, 'videos'),
            os.path.join(self.upload_folder, 'audio'),
            os.path.join(self.upload_folder, 'financials'),
            os.path.join(self.upload_folder, 'demos'),
            os.path.join(self.upload_folder, 'updates'),
            os.path.join(self.upload_folder, 'supporting'),
            os.path.join(self.upload_folder, 'images'),
            os.path.join(self.upload_folder, 'documents')
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
        
        self._directories_ensured = True
    
    def _get_subfolder(self, file_type: str) -> str:
        """Map file type to a storage subfolder"""
        subfolder_map = {
            'pitch_deck': 'pitch_decks',
            'video_pitch': 'videos',
            'audio_pitch': 'audio',
            'financial_model': 'financials',
            'product_demo': 'demos',
            'founder_update': 'updates',
            'supporting_document': 'supporting',
            'image': 'images',
            'document': 'documents'
        }
        return subfolder_map.get(file_type, 'documents')

    def get_upload_path(self, file_type: str, filename: str) -> str:
        """Get the upload path for a specific file type"""
        self._ensure_upload_directories()
        subfolder = self._get_subfolder(file_type)
        return os.path.join(self.upload_folder, subfolder, filename)
    
    def validate_file(self, file, file_type: str) -> Dict[str, Any]:
        """Validate uploaded file"""
        if not file or not file.filename:
            return {'valid': False, 'error': 'No file provided'}
        
        # Check file extension
        if not self._is_allowed_file(file.filename, file_type):
            allowed_exts = ', '.join(self.ALLOWED_EXTENSIONS.get(file_type, []))
            return {
                'valid': False, 
                'error': f'File type not allowed. Allowed types: {allowed_exts}'
            }
        
        # Check file size
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        file.seek(0)  # Reset to beginning
        
        max_size = self.MAX_FILE_SIZES.get(file_type, 20) * 1024 * 1024  # Convert to bytes
        if file_size > max_size:
            return {
                'valid': False,
                'error': f'File too large. Maximum size: {max_size // (1024*1024)}MB'
            }
        
        return {'valid': True, 'file_size': file_size}
    
    def _is_allowed_file(self, filename: str, file_type: str) -> bool:
        """Check if file extension is allowed for the given file type"""
        if not filename or '.' not in filename:
            return False
        
        extension = filename.rsplit('.', 1)[1].lower()
        allowed_extensions = self.ALLOWED_EXTENSIONS.get(file_type, [])
        return extension in allowed_extensions
    
    def save_file(self, file, file_type: str, startup_id: str) -> Dict[str, Any]:
        """Save uploaded file and return file info"""
        try:
            # Ensure directories exist
            self._ensure_upload_directories()
            
            # Validate file
            validation = self.validate_file(file, file_type)
            if not validation['valid']:
                return validation
            
            # Generate unique filename
            file_extension = file.filename.rsplit('.', 1)[1].lower()
            unique_filename = f"{startup_id}_{file_type}_{uuid.uuid4().hex[:8]}.{file_extension}"
            secure_name = secure_filename(unique_filename)
            
            # Get upload path
            subfolder = self._get_subfolder(file_type)
            upload_path = self.get_upload_path(file_type, secure_name)
            
            # Save file
            file.save(upload_path)
            
            # Get file info
            file_size = validation['file_size']
            mime_type = mimetypes.guess_type(upload_path)[0] or 'application/octet-stream'
            
            relative_web_path = os.path.join(subfolder, secure_name).replace(os.sep, '/')

            return {
                'valid': True,
                'filename': secure_name,
                'original_filename': file.filename,
                'file_path': upload_path,
                'file_size': file_size,
                'mime_type': mime_type,
                'file_type': file_type,
                'url': f"/uploads/{relative_web_path}"  # Public URL preserving subfolder structure
            }
            
        except Exception as e:
            logger.error(f"Error saving file: {e}")
            return {'valid': False, 'error': f'Failed to save file: {str(e)}'}
    
    def delete_file(self, file_path: str) -> bool:
        """Delete a file from the filesystem"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {e}")
            return False
    
    def get_file_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Get information about a file"""
        try:
            if not os.path.exists(file_path):
                return None
            
            stat = os.stat(file_path)
            return {
                'file_path': file_path,
                'file_size': stat.st_size,
                'created_at': stat.st_ctime,
                'modified_at': stat.st_mtime,
                'exists': True
            }
        except Exception as e:
            logger.error(f"Error getting file info for {file_path}: {e}")
            return None
    
    def cleanup_orphaned_files(self, startup_id: str) -> int:
        """Clean up files that are no longer referenced by any startup"""
        # This would be implemented to clean up files that are no longer referenced
        # For now, just return 0
        return 0


# Global file upload service instance
file_upload_service = FileUploadService()
