"""
Encryption Service - Handles data encryption and decryption
"""

import base64
import hashlib
import hmac
import logging
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from typing import Dict, Any, Optional
import json
import os

logger = logging.getLogger(__name__)

class EncryptionService:
    """Service for encrypting and decrypting sensitive data"""
    
    def __init__(self):
        self.master_key = self._get_or_create_master_key()
        self.fernet = Fernet(self.master_key)
    
    def _get_or_create_master_key(self) -> bytes:
        """Get or create master encryption key"""
        try:
            key_file = "encryption.key"
            
            if os.path.exists(key_file):
                with open(key_file, 'rb') as f:
                    return f.read()
            else:
                # Generate new key
                key = Fernet.generate_key()
                with open(key_file, 'wb') as f:
                    f.write(key)
                return key
                
        except Exception as e:
            logger.error(f"Failed to get master key: {str(e)}")
            # Fallback to generated key (not persistent)
            return Fernet.generate_key()
    
    def encrypt_data(self, data: Any) -> str:
        """Encrypt any data type"""
        try:
            # Convert to JSON string
            json_data = json.dumps(data, default=str)
            
            # Encrypt
            encrypted_data = self.fernet.encrypt(json_data.encode())
            
            # Return base64 encoded string
            return base64.b64encode(encrypted_data).decode()
            
        except Exception as e:
            logger.error(f"Encryption failed: {str(e)}")
            return str(data)  # Fallback to plain text
    
    def decrypt_data(self, encrypted_data: str) -> Any:
        """Decrypt data back to original format"""
        try:
            # Decode base64
            encrypted_bytes = base64.b64decode(encrypted_data.encode())
            
            # Decrypt
            decrypted_bytes = self.fernet.decrypt(encrypted_bytes)
            
            # Parse JSON
            json_data = decrypted_bytes.decode()
            return json.loads(json_data)
            
        except Exception as e:
            logger.error(f"Decryption failed: {str(e)}")
            return encrypted_data  # Return as-is if decryption fails
    
    def hash_data(self, data: str) -> str:
        """Create secure hash of data"""
        try:
            return hashlib.sha256(data.encode()).hexdigest()
        except Exception as e:
            logger.error(f"Hashing failed: {str(e)}")
            return data
    
    def verify_hash(self, data: str, hash_value: str) -> bool:
        """Verify data against hash"""
        try:
            return self.hash_data(data) == hash_value
        except Exception as e:
            logger.error(f"Hash verification failed: {str(e)}")
            return False
    
    def encrypt_sensitive_fields(self, data: Dict, sensitive_fields: list) -> Dict:
        """Encrypt specific fields in a dictionary"""
        try:
            encrypted_data = data.copy()
            
            for field in sensitive_fields:
                if field in encrypted_data:
                    encrypted_data[field] = self.encrypt_data(encrypted_data[field])
            
            return encrypted_data
            
        except Exception as e:
            logger.error(f"Field encryption failed: {str(e)}")
            return data
    
    def decrypt_sensitive_fields(self, data: Dict, sensitive_fields: list) -> Dict:
        """Decrypt specific fields in a dictionary"""
        try:
            decrypted_data = data.copy()
            
            for field in sensitive_fields:
                if field in decrypted_data:
                    decrypted_data[field] = self.decrypt_data(decrypted_data[field])
            
            return decrypted_data
            
        except Exception as e:
            logger.error(f"Field decryption failed: {str(e)}")
            return data