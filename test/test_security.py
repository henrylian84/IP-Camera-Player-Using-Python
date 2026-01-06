"""
Test script for camera security features.

This script tests password encryption/decryption and secure credential handling.
"""

import sys
from camera_security import encrypt_password, decrypt_password, PasswordEncryption


def test_password_encryption():
    """Test basic password encryption and decryption."""
    print("Testing password encryption/decryption...")
    
    # Test with various passwords
    test_passwords = [
        "simple",
        "Complex!Pass@123",
        "unicode_测试_пароль",
        "",  # Empty password
        "a" * 100,  # Long password
    ]
    
    for password in test_passwords:
        # Encrypt
        encrypted = encrypt_password(password)
        
        # Decrypt
        decrypted = decrypt_password(encrypted)
        
        # Verify
        assert decrypted == password, f"Decryption failed for password: {password[:10]}..."
        
        if password:
            # Ensure encrypted is different from original
            assert encrypted != password, "Encrypted password should differ from original"
            
            # Ensure encrypted is base64-like
            assert PasswordEncryption.is_encrypted(encrypted), "Encrypted password should be base64"
        else:
            # Empty password should remain empty
            assert encrypted == "", "Empty password should remain empty"
        
        print(f"  ✓ Password encryption/decryption successful (length: {len(password)})")
    
    print("✓ Password encryption tests passed\n")


def test_encryption_consistency():
    """Test that encryption is consistent."""
    print("Testing encryption consistency...")
    
    password = "TestPassword123"
    
    # Encrypt multiple times
    encrypted1 = encrypt_password(password)
    encrypted2 = encrypt_password(password)
    
    # Should produce same result (deterministic encryption)
    assert encrypted1 == encrypted2, "Encryption should be deterministic"
    
    # Both should decrypt to same password
    assert decrypt_password(encrypted1) == password
    assert decrypt_password(encrypted2) == password
    
    print("  ✓ Encryption is consistent")
    print("✓ Encryption consistency tests passed\n")


def test_invalid_decryption():
    """Test decryption of invalid data."""
    print("Testing invalid decryption handling...")
    
    # Test with invalid base64
    result = decrypt_password("not-valid-base64!!!")
    assert result == "", "Invalid encrypted data should return empty string"
    print("  ✓ Invalid base64 handled correctly")
    
    # Test with empty string
    result = decrypt_password("")
    assert result == "", "Empty string should return empty string"
    print("  ✓ Empty string handled correctly")
    
    # Test with None (should handle gracefully)
    try:
        result = decrypt_password(None)
        # If it doesn't raise an exception, it should return empty string
        assert result == "", "None should return empty string"
        print("  ✓ None handled correctly")
    except (TypeError, AttributeError):
        # It's also acceptable to raise an exception for None
        print("  ✓ None raises exception (acceptable)")
    
    print("✓ Invalid decryption tests passed\n")


def test_is_encrypted():
    """Test the is_encrypted heuristic."""
    print("Testing is_encrypted heuristic...")
    
    # Plain text passwords should not be detected as encrypted
    assert not PasswordEncryption.is_encrypted("password123"), "Plain text should not be detected as encrypted"
    assert not PasswordEncryption.is_encrypted(""), "Empty string should not be detected as encrypted"
    
    # Encrypted passwords should be detected
    encrypted = encrypt_password("test")
    assert PasswordEncryption.is_encrypted(encrypted), "Encrypted password should be detected"
    
    print("  ✓ is_encrypted heuristic works correctly")
    print("✓ is_encrypted tests passed\n")


def test_security_guidelines():
    """Test that security guidelines are followed."""
    print("Testing security guidelines...")
    
    password = "SecretPassword123"
    encrypted = encrypt_password(password)
    
    # Verify password is not in plain text in encrypted form
    assert password not in encrypted, "Plain text password should not appear in encrypted form"
    
    # Verify encrypted password is different from original
    assert encrypted != password, "Encrypted password should differ from original"
    
    # Verify we can decrypt back
    decrypted = decrypt_password(encrypted)
    assert decrypted == password, "Decryption should recover original password"
    
    print("  ✓ Password is properly encrypted")
    print("  ✓ Plain text password not visible in encrypted form")
    print("  ✓ Decryption recovers original password")
    print("✓ Security guidelines tests passed\n")


def main():
    """Run all security tests."""
    print("="*60)
    print("Running Camera Security Tests")
    print("="*60 + "\n")
    
    try:
        test_password_encryption()
        test_encryption_consistency()
        test_invalid_decryption()
        test_is_encrypted()
        test_security_guidelines()
        
        print("="*60)
        print("✓ All security tests passed!")
        print("="*60)
        return 0
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
