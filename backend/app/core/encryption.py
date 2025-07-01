# backend/app/core/encryption.py
"""
Secure credential encryption and decryption for API testing platform.
Uses AES-256-GCM for authenticated encryption with key derivation from master password.
"""

import json
import os
import base64
from typing import Any, Dict, Optional, Union
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.backends import default_backend
import secrets

from .exceptions import EncryptionError


class CredentialEncryption:
    """
    Handles secure encryption and decryption of API credentials.
    
    Features:
    - AES-256-GCM authenticated encryption
    - PBKDF2 key derivation from master password
    - Salt-based protection against rainbow table attacks
    - Secure random nonce generation for each encryption
    """
    
    def __init__(self, master_password: Optional[str] = None):
        self.master_password = master_password
        self._key_cache: Optional[bytes] = None
        
    def _derive_key(self, password: str, salt: bytes) -> bytes:
        """Derive encryption key from password using PBKDF2."""
        try:
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,  # 256 bits
                salt=salt,
                iterations=100000,  # OWASP recommended minimum
                backend=default_backend()
            )
            return kdf.derive(password.encode('utf-8'))
        except Exception as e:
            raise EncryptionError("key_derivation", str(e))
            
    def set_master_password(self, password: str) -> None:
        """Set the master password for encryption/decryption."""
        self.master_password = password
        self._key_cache = None  # Clear cache when password changes
        
    def encrypt_credentials(
        self, 
        credentials: Dict[str, Any], 
        password: Optional[str] = None
    ) -> str:
        """
        Encrypt credentials dictionary to base64-encoded string.
        
        Args:
            credentials: Dictionary of credential data to encrypt
            password: Optional password override (uses master_password if not provided)
            
        Returns:
            Base64-encoded encrypted data with embedded salt and nonce
            
        Raises:
            EncryptionError: If encryption fails
        """
        if not password and not self.master_password:
            raise EncryptionError("encrypt", "No password provided")
            
        try:
            # Use provided password or master password
            pwd = password or self.master_password
            
            # Generate random salt and nonce
            salt = secrets.token_bytes(32)  # 256-bit salt
            nonce = secrets.token_bytes(12)  # 96-bit nonce for GCM
            
            # Derive key from password
            key = self._derive_key(pwd, salt)
            
            # Serialize credentials to JSON
            plaintext = json.dumps(credentials, separators=(',', ':')).encode('utf-8')
            
            # Encrypt with AES-GCM
            aesgcm = AESGCM(key)
            ciphertext = aesgcm.encrypt(nonce, plaintext, None)
            
            # Combine salt + nonce + ciphertext
            encrypted_data = salt + nonce + ciphertext
            
            # Return base64-encoded result
            return base64.b64encode(encrypted_data).decode('ascii')
            
        except Exception as e:
            if isinstance(e, EncryptionError):
                raise
            raise EncryptionError("encrypt", str(e))
            
    def decrypt_credentials(
        self, 
        encrypted_data: str, 
        password: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Decrypt base64-encoded credentials string.
        
        Args:
            encrypted_data: Base64-encoded encrypted credentials
            password: Optional password override (uses master_password if not provided)
            
        Returns:
            Decrypted credentials dictionary
            
        Raises:
            EncryptionError: If decryption fails
        """
        if not password and not self.master_password:
            raise EncryptionError("decrypt", "No password provided")
            
        try:
            # Use provided password or master password
            pwd = password or self.master_password
            
            # Decode from base64
            data = base64.b64decode(encrypted_data.encode('ascii'))
            
            # Extract components (salt: 32 bytes, nonce: 12 bytes, rest: ciphertext)
            if len(data) < 44:  # 32 + 12 minimum
                raise ValueError("Invalid encrypted data format")
                
            salt = data[:32]
            nonce = data[32:44]
            ciphertext = data[44:]
            
            # Derive key from password
            key = self._derive_key(pwd, salt)
            
            # Decrypt with AES-GCM
            aesgcm = AESGCM(key)
            plaintext = aesgcm.decrypt(nonce, ciphertext, None)
            
            # Parse JSON
            credentials = json.loads(plaintext.decode('utf-8'))
            
            return credentials
            
        except Exception as e:
            if isinstance(e, EncryptionError):
                raise
            raise EncryptionError("decrypt", str(e))
            
    def verify_password(self, encrypted_data: str, password: str) -> bool:
        """
        Verify if a password can decrypt the given encrypted data.
        
        Args:
            encrypted_data: Base64-encoded encrypted data
            password: Password to verify
            
        Returns:
            True if password is correct, False otherwise
        """
        try:
            self.decrypt_credentials(encrypted_data, password)
            return True
        except EncryptionError:
            return False


class CredentialManager:
    """
    High-level credential management with file-based storage.
    """
    
    def __init__(self, storage_dir: str, master_password: Optional[str] = None):
        self.storage_dir = storage_dir
        self.encryption = CredentialEncryption(master_password)
        
        # Ensure storage directory exists
        os.makedirs(storage_dir, exist_ok=True)
        
    def _get_credential_file(self, service_name: str, environment: str = "default") -> str:
        """Get the file path for storing service credentials."""
        filename = f"{service_name}_{environment}.enc"
        return os.path.join(self.storage_dir, filename)
        
    def store_credentials(
        self, 
        service_name: str, 
        credentials: Dict[str, Any],
        environment: str = "default"
    ) -> None:
        """
        Store encrypted credentials for a service.
        
        Args:
            service_name: Name of the service (e.g., 'stripe', 'brevo')
            credentials: Credential data to store
            environment: Environment name (e.g., 'production', 'sandbox')
        """
        try:
            # Add metadata
            credential_data = {
                "service": service_name,
                "environment": environment,
                "credentials": credentials,
                "created_at": secrets.token_hex(8),  # Simple timestamp alternative
                "version": "1.0"
            }
            
            # Encrypt credentials
            encrypted_data = self.encryption.encrypt_credentials(credential_data)
            
            # Write to file
            file_path = self._get_credential_file(service_name, environment)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(encrypted_data)
                
        except Exception as e:
            raise EncryptionError("store", f"Failed to store credentials: {str(e)}")
            
    def load_credentials(
        self, 
        service_name: str, 
        environment: str = "default"
    ) -> Optional[Dict[str, Any]]:
        """
        Load and decrypt credentials for a service.
        
        Args:
            service_name: Name of the service
            environment: Environment name
            
        Returns:
            Decrypted credentials or None if not found
        """
        try:
            file_path = self._get_credential_file(service_name, environment)
            
            if not os.path.exists(file_path):
                return None
                
            # Read encrypted data
            with open(file_path, 'r', encoding='utf-8') as f:
                encrypted_data = f.read().strip()
                
            # Decrypt and return credentials
            credential_data = self.encryption.decrypt_credentials(encrypted_data)
            return credential_data.get("credentials")
            
        except Exception as e:
            raise EncryptionError("load", f"Failed to load credentials: {str(e)}")
            
    def delete_credentials(
        self, 
        service_name: str, 
        environment: str = "default"
    ) -> bool:
        """
        Delete stored credentials for a service.
        
        Args:
            service_name: Name of the service
            environment: Environment name
            
        Returns:
            True if credentials were deleted, False if not found
        """
        try:
            file_path = self._get_credential_file(service_name, environment)
            
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
            
        except Exception as e:
            raise EncryptionError("delete", f"Failed to delete credentials: {str(e)}")
            
    def list_stored_credentials(self) -> Dict[str, list]:
        """
        List all stored credentials by service.
        
        Returns:
            Dictionary mapping service names to list of environments
        """
        try:
            credentials = {}
            
            if not os.path.exists(self.storage_dir):
                return credentials
                
            for filename in os.listdir(self.storage_dir):
                if filename.endswith('.enc'):
                    # Parse filename: service_environment.enc
                    name_parts = filename[:-4].split('_')
                    if len(name_parts) >= 2:
                        service = '_'.join(name_parts[:-1])
                        environment = name_parts[-1]
                        
                        if service not in credentials:
                            credentials[service] = []
                        credentials[service].append(environment)
                        
            return credentials
            
        except Exception as e:
            raise EncryptionError("list", f"Failed to list credentials: {str(e)}")
            
    def set_master_password(self, password: str) -> None:
        """Set the master password for encryption/decryption."""
        self.encryption.set_master_password(password)