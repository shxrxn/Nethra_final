"""
Security Utilities - Security-related helper functions
"""

import hashlib
import hmac
import jwt
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
import secrets
import bcrypt

logger = logging.getLogger(__name__)

class SecurityUtils:
    """Security utility functions"""
    
    # Use a secret key for JWT (in production, use environment variable)
    SECRET_KEY = "nethra_secret_key_change_in_production"
    ALGORITHM = "HS256"
    
    @staticmethod
    def generate_token(user_id: str, expires_in: timedelta = timedelta(hours=24)) -> str:
        """Generate JWT token for user"""
        try:
            payload = {
                "user_id": user_id,
                "exp": datetime.utcnow() + expires_in,
                "iat": datetime.utcnow()
            }
            
            token = jwt.encode(payload, SecurityUtils.SECRET_KEY, algorithm=SecurityUtils.ALGORITHM)
            return token
            
        except Exception as e:
            logger.error(f"Token generation failed: {str(e)}")
            raise
    
    @staticmethod
    def validate_token(token: str) -> Dict[str, Any]:
        """Validate JWT token and return user info"""
        try:
            payload = jwt.decode(token, SecurityUtils.SECRET_KEY, algorithms=[SecurityUtils.ALGORITHM])
            return {
                "user_id": payload.get("user_id"),
                "expires_at": payload.get("exp")
            }
            
        except jwt.ExpiredSignatureError:
            raise Exception("Token has expired")
        except jwt.InvalidTokenError:
            raise Exception("Invalid token")
        except Exception as e:
            logger.error(f"Token validation failed: {str(e)}")
            raise
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt"""
        try:
            salt = bcrypt.gensalt()
            hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
            return hashed.decode('utf-8')
            
        except Exception as e:
            logger.error(f"Password hashing failed: {str(e)}")
            raise
    
    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Verify password against hash"""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
            
        except Exception as e:
            logger.error(f"Password verification failed: {str(e)}")
            return False
    
    @staticmethod
    def generate_secure_random(length: int = 32) -> str:
        """Generate secure random string"""
        try:
            return secrets.token_urlsafe(length)
            
        except Exception as e:
            logger.error(f"Secure random generation failed: {str(e)}")
            return secrets.token_hex(16)
    
    @staticmethod
    def create_hmac_signature(data: str, secret: str) -> str:
        """Create HMAC signature for data"""
        try:
            signature = hmac.new(
                secret.encode('utf-8'),
                data.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            return signature
            
        except Exception as e:
            logger.error(f"HMAC signature creation failed: {str(e)}")
            raise
    
    @staticmethod
    def verify_hmac_signature(data: str, signature: str, secret: str) -> bool:
        """Verify HMAC signature"""
        try:
            expected_signature = SecurityUtils.create_hmac_signature(data, secret)
            return hmac.compare_digest(signature, expected_signature)
            
        except Exception as e:
            logger.error(f"HMAC signature verification failed: {str(e)}")
            return False
    
    @staticmethod
    async def log_security_incident(user_id: str, incident_type: str, details: Dict):
        """Log security incident"""
        try:
            incident_log = {
                "user_id": user_id,
                "incident_type": incident_type,
                "details": details,
                "timestamp": datetime.utcnow().isoformat(),
                "severity": details.get("severity", "MEDIUM")
            }
            
            logger.warning(f"Security incident: {incident_log}")
            
            # In a real implementation, this would store to database
            # For now, just log it
            
        except Exception as e:
            logger.error(f"Failed to log security incident: {str(e)}")
    
    @staticmethod
    def sanitize_input(input_data: str) -> str:
        """Sanitize user input to prevent injection attacks"""
        try:
            # Remove potentially dangerous characters
            dangerous_chars = ['<', '>', '"', "'", '&', ';', '(', ')', '|', '`']
            
            sanitized = input_data
            for char in dangerous_chars:
                sanitized = sanitized.replace(char, '')
            
            return sanitized.strip()
            
        except Exception as e:
            logger.error(f"Input sanitization failed: {str(e)}")
            return ""
    
    @staticmethod
    def validate_session_token(token: str) -> bool:
        """Validate session token format"""
        try:
            # Basic token format validation
            if not token or len(token) < 10:
                return False
            
            # Check if token contains only valid characters
            valid_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.')
            return all(c in valid_chars for c in token)
            
        except Exception as e:
            logger.error(f"Session token validation failed: {str(e)}")
            return False