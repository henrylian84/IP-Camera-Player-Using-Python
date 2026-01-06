"""
Camera Security Module

This module provides password encryption and decryption functionality for
secure storage of camera credentials. It uses a combination of base64 encoding
and XOR cipher for password obfuscation.

SECURITY GUIDELINES:
1. Never log plain text passwords
2. Never log encrypted passwords (they can be decrypted)
3. Never log URLs containing credentials
4. Always use password masking in UI (QLineEdit.Password mode)
5. Clear password fields after use where appropriate

Note: For production environments, consider using the cryptography library
with proper key management for stronger encryption.

Author: Yamil Garcia
Version: 1.0.0
"""

import base64
import hashlib
from typing import Optional


class PasswordEncryption:
    """
    Handles password encryption and decryption for camera credentials.
    
    This class provides methods to encrypt passwords before storage and
    decrypt them when needed for camera connections. It uses a machine-specific
    key derived from system information to provide basic security.
    
    The encryption is designed to prevent casual viewing of passwords in
    settings files, but is not intended for high-security applications.
    For production use, consider using proper encryption libraries like
    cryptography with secure key management.
    """
    
    # Static key derived from application-specific data
    # In production, this should be stored securely or derived from system info
    _APP_KEY = "IPCameraPlayer_SecureKey_v1.0"
    
    @classmethod
    def _get_encryption_key(cls) -> bytes:
        """
        Generate encryption key from application-specific data.
        
        Returns:
            Bytes representing the encryption key
        """
        # Create a hash of the app key to use as encryption key
        key_hash = hashlib.sha256(cls._APP_KEY.encode()).digest()
        return key_hash
    
    @classmethod
    def _xor_encrypt_decrypt(cls, data: bytes, key: bytes) -> bytes:
        """
        Perform XOR encryption/decryption.
        
        XOR is symmetric, so the same function works for both encryption
        and decryption.
        
        Args:
            data: Data to encrypt/decrypt
            key: Encryption key
            
        Returns:
            Encrypted/decrypted data
        """
        # Repeat key to match data length
        key_repeated = (key * (len(data) // len(key) + 1))[:len(data)]
        
        # XOR each byte
        result = bytes(a ^ b for a, b in zip(data, key_repeated))
        return result
    
    @classmethod
    def encrypt_password(cls, password: str) -> str:
        """
        Encrypt a password for secure storage.
        
        Args:
            password: Plain text password to encrypt
            
        Returns:
            Encrypted password as base64-encoded string
            Returns empty string if password is empty
        """
        if not password:
            return ""
        
        try:
            # Convert password to bytes
            password_bytes = password.encode('utf-8')
            
            # Get encryption key
            key = cls._get_encryption_key()
            
            # Encrypt using XOR
            encrypted_bytes = cls._xor_encrypt_decrypt(password_bytes, key)
            
            # Encode to base64 for safe storage
            encrypted_b64 = base64.b64encode(encrypted_bytes).decode('ascii')
            
            return encrypted_b64
            
        except Exception as e:
            print(f"Error encrypting password: {e}")
            # Return empty string on error to avoid storing plain text
            return ""
    
    @classmethod
    def decrypt_password(cls, encrypted_password: str) -> str:
        """
        Decrypt a password from storage.
        
        Args:
            encrypted_password: Base64-encoded encrypted password
            
        Returns:
            Decrypted plain text password
            Returns empty string if decryption fails or input is empty
        """
        if not encrypted_password:
            return ""
        
        try:
            # Decode from base64
            encrypted_bytes = base64.b64decode(encrypted_password.encode('ascii'))
            
            # Get encryption key
            key = cls._get_encryption_key()
            
            # Decrypt using XOR (same operation as encryption)
            decrypted_bytes = cls._xor_encrypt_decrypt(encrypted_bytes, key)
            
            # Convert back to string
            password = decrypted_bytes.decode('utf-8')
            
            return password
            
        except Exception as e:
            print(f"Error decrypting password: {e}")
            # Return empty string on error
            return ""
    
    @classmethod
    def is_encrypted(cls, password: str) -> bool:
        """
        Check if a password string appears to be encrypted.
        
        This is a heuristic check based on base64 encoding characteristics.
        
        Args:
            password: Password string to check
            
        Returns:
            True if password appears to be encrypted, False otherwise
        """
        if not password:
            return False
        
        try:
            # Try to decode as base64
            base64.b64decode(password.encode('ascii'))
            
            # Check if it contains only base64 characters
            valid_chars = set('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=')
            return all(c in valid_chars for c in password)
            
        except Exception:
            return False


def encrypt_password(password: str) -> str:
    """
    Convenience function to encrypt a password.
    
    Args:
        password: Plain text password
        
    Returns:
        Encrypted password string
    """
    return PasswordEncryption.encrypt_password(password)


def decrypt_password(encrypted_password: str) -> str:
    """
    Convenience function to decrypt a password.
    
    Args:
        encrypted_password: Encrypted password string
        
    Returns:
        Plain text password
    """
    return PasswordEncryption.decrypt_password(encrypted_password)
