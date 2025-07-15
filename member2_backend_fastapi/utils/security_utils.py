"""
Security Utilities for NETHRA Backend
"""

import hashlib
import hmac
import secrets
import base64
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)

class SecurityUtils:
    """Security utility functions for NETHRA"""
    
    def __init__(self):
        self.secret_key = self._generate_secret_key()
        self.cipher_suite = Fernet(self.secret_key)
    
    def _generate_secret_key(self) -> bytes:
        """Generate or load secret key for encryption"""
        # In production, load from secure environment variable
        password = b"nethra_security_key_2024"
        salt = b"nethra_salt_2024"
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(password))
        return key
    
    def encrypt_data(self, data: str) -> str:
        """Encrypt sensitive data"""
        try:
            encrypted_data = self.cipher_suite.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted_data).decode()
        except Exception as e:
            logger.error(f"Encryption failed: {str(e)}")
            raise
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        try:
            decoded_data = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted_data = self.cipher_suite.decrypt(decoded_data)
            return decrypted_data.decode()
        except Exception as e:
            logger.error(f"Decryption failed: {str(e)}")
            raise
    
    def hash_password(self, password: str, salt: Optional[str] = None) -> tuple[str, str]:
        """Hash password with salt"""
        if salt is None:
            salt = secrets.token_hex(16)
        
        password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        )
        
        return password_hash.hex(), salt
    
    def verify_password(self, password: str, password_hash: str, salt: str) -> bool:
        """Verify password against hash"""
        try:
            computed_hash, _ = self.hash_password(password, salt)
            return hmac.compare_digest(computed_hash, password_hash)
        except Exception as e:
            logger.error(f"Password verification failed: {str(e)}")
            return False
    
    def generate_session_token(self) -> str:
        """Generate secure session token"""
        return secrets.token_urlsafe(32)
    
    def generate_api_key(self) -> str:
        """Generate API key"""
        return secrets.token_urlsafe(48)
    
    def create_hmac_signature(self, data: str, secret: str) -> str:
        """Create HMAC signature for data integrity"""
        signature = hmac.new(
            secret.encode('utf-8'),
            data.encode('utf-8'),
            hashlib.sha256
        )
        return signature.hexdigest()
    
    def verify_hmac_signature(self, data: str, signature: str, secret: str) -> bool:
        """Verify HMAC signature"""
        expected_signature = self.create_hmac_signature(data, secret)
        return hmac.compare_digest(signature, expected_signature)
    
    def sanitize_input(self, input_data: Any) -> Any:
        """Sanitize input data to prevent injection attacks"""
        if isinstance(input_data, str):
            # Remove potentially dangerous characters
            dangerous_chars = ['<', '>', '"', "'", '&', ';', '(', ')', '|', '`']
            sanitized = input_data
            for char in dangerous_chars:
                sanitized = sanitized.replace(char, '')
            return sanitized.strip()
        elif isinstance(input_data, dict):
            return {key: self.sanitize_input(value) for key, value in input_data.items()}
        elif isinstance(input_data, list):
            return [self.sanitize_input(item) for item in input_data]
        else:
            return input_data
    
    def validate_session_token(self, token: str) -> bool:
        """Validate session token format"""
        if not token or len(token) < 32:
            return False
        
        # Check if token contains only valid characters
        try:
            base64.urlsafe_b64decode(token + '==')
            return True
        except Exception:
            return False
    
    def is_rate_limited(self, identifier: str, max_requests: int = 100, 
                       time_window: int = 3600) -> bool:
        """Simple rate limiting check"""
        # In production, use Redis or similar for distributed rate limiting
        # This is a simplified in-memory implementation
        current_time = datetime.now()
        
        # For demo purposes, always return False (no rate limiting)
        return False
    
    def generate_csrf_token(self) -> str:
        """Generate CSRF token"""
        return secrets.token_urlsafe(32)
    
    def validate_csrf_token(self, token: str, expected_token: str) -> bool:
        """Validate CSRF token"""
        return hmac.compare_digest(token, expected_token)
    
    def secure_random_string(self, length: int = 16) -> str:
        """Generate secure random string"""
        return secrets.token_urlsafe(length)
    
    def hash_data(self, data: str) -> str:
        """Hash data using SHA-256"""
        return hashlib.sha256(data.encode()).hexdigest()
    
    def constant_time_compare(self, a: str, b: str) -> bool:
        """Constant time string comparison to prevent timing attacks"""
        return hmac.compare_digest(a, b)
    
    def validate_input_length(self, input_data: str, max_length: int = 1000) -> bool:
        """Validate input length to prevent DoS attacks"""
        return len(input_data) <= max_length
    
    def escape_html(self, text: str) -> str:
        """Escape HTML characters"""
        html_escape_table = {
            "&": "&amp;",
            '"': "&quot;",
            "'": "&#x27;",
            ">": "&gt;",
            "<": "&lt;",
        }
        return "".join(html_escape_table.get(c, c) for c in text)
    
    def generate_nonce(self) -> str:
        """Generate cryptographic nonce"""
        return secrets.token_hex(16)
    
    def create_secure_headers(self) -> Dict[str, str]:
        """Create security headers for HTTP responses"""
        return {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'",
            "Referrer-Policy": "strict-origin-when-cross-origin"
        }
    
    def log_security_event(self, event_type: str, details: Dict[str, Any], 
                          severity: str = "INFO"):
        """Log security events"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "severity": severity,
            "details": details
        }
        
        if severity == "CRITICAL":
            logger.critical(f"Security Event: {log_entry}")
        elif severity == "ERROR":
            logger.error(f"Security Event: {log_entry}")
        elif severity == "WARNING":
            logger.warning(f"Security Event: {log_entry}")
        else:
            logger.info(f"Security Event: {log_entry}")

# Global security utils instance
security_utils = SecurityUtils()