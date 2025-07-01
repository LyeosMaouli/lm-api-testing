# tests/test_encryption.py
"""
Test the encryption system.
"""

import pytest
import tempfile
from backend.app.core.encryption import CredentialEncryption, CredentialManager

def test_credential_encryption():
    """Test basic encryption and decryption."""
    encryption = CredentialEncryption("test_password")
    
    test_data = {
        "api_key": "test_key_123",
        "secret": "super_secret_value"
    }
    
    # Encrypt
    encrypted = encryption.encrypt_credentials(test_data)
    assert isinstance(encrypted, str)
    assert len(encrypted) > 0
    
    # Decrypt
    decrypted = encryption.decrypt_credentials(encrypted)
    assert decrypted == test_data

def test_credential_encryption_wrong_password():
    """Test decryption with wrong password fails."""
    encryption = CredentialEncryption("correct_password")
    
    test_data = {"api_key": "test_key"}
    encrypted = encryption.encrypt_credentials(test_data)
    
    # Try to decrypt with wrong password
    wrong_encryption = CredentialEncryption("wrong_password")
    
    with pytest.raises(Exception):  # Should raise EncryptionError
        wrong_encryption.decrypt_credentials(encrypted)

def test_credential_manager():
    """Test credential manager functionality."""
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = CredentialManager(temp_dir, "test_password")
        
        # Store credentials
        test_creds = {"api_key": "test_key_123"}
        manager.store_credentials("test_service", test_creds, "production")
        
        # Load credentials
        loaded_creds = manager.load_credentials("test_service", "production")
        assert loaded_creds == test_creds
        
        # List stored credentials
        stored = manager.list_stored_credentials()
        assert "test_service" in stored
        assert "production" in stored["test_service"]