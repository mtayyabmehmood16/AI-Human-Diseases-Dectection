"""
Security utilities for the Medical Management System.
Includes input validation, password strength checking, and sanitization.
"""
import re
from typing import Optional
from werkzeug.security import safe_str_cmp
import html


class PasswordValidator:
    """Validate password strength."""
    
    MIN_LENGTH = 8
    
    @staticmethod
    def validate(password: str) -> tuple[bool, Optional[str]]:
        """
        Validate password strength.
        
        Returns:
            (is_valid, error_message)
        """
        if len(password) < PasswordValidator.MIN_LENGTH:
            return False, f"Password must be at least {PasswordValidator.MIN_LENGTH} characters long"
        
        if not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"
        
        if not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"
        
        if not re.search(r'\d', password):
            return False, "Password must contain at least one digit"
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "Password must contain at least one special character"
        
        return True, None


class InputSanitizer:
    """Sanitize user input to prevent XSS and injection attacks."""
    
    @staticmethod
    def sanitize_html(text: str) -> str:
        """Escape HTML characters to prevent XSS."""
        if not text:
            return ""
        return html.escape(text)
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename to prevent directory traversal."""
        if not filename:
            return ""
        # Remove path separators and dangerous characters
        filename = re.sub(r'[/\\]', '', filename)
        filename = re.sub(r'[^\w\s.-]', '', filename)
        return filename.strip()
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format."""
        if not email:
            return False
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))


def allowed_file(filename: str, allowed_extensions: set) -> bool:
    """Check if file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions


def get_file_extension(filename: str) -> str:
    """Get file extension safely."""
    if '.' in filename:
        return filename.rsplit('.', 1)[1].lower()
    return ''
