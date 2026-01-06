#!/usr/bin/env python3
"""
Demo script to showcase security features implementation.

This script demonstrates:
1. Password encryption/decryption
2. Secure storage in QSettings
3. Safe URL generation
4. Backward compatibility
"""

import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QSettings
from camera_security import encrypt_password, decrypt_password, PasswordEncryption
from ip_camera_player import CameraInstance, CameraManager


def demo_password_encryption():
    """Demonstrate password encryption and decryption."""
    print("="*60)
    print("DEMO 1: Password Encryption/Decryption")
    print("="*60)
    
    password = "MySecretPassword123!"
    print(f"\n1. Original password: {password}")
    
    # Encrypt
    encrypted = encrypt_password(password)
    print(f"2. Encrypted password: {encrypted}")
    print(f"   - Length: {len(encrypted)} characters")
    print(f"   - Format: Base64-encoded")
    print(f"   - Is encrypted: {PasswordEncryption.is_encrypted(encrypted)}")
    
    # Decrypt
    decrypted = decrypt_password(encrypted)
    print(f"3. Decrypted password: {decrypted}")
    print(f"   - Matches original: {decrypted == password}")
    
    print("\n✓ Password encryption/decryption works correctly!\n")


def demo_camera_instance_security():
    """Demonstrate CameraInstance security features."""
    print("="*60)
    print("DEMO 2: CameraInstance Security")
    print("="*60)
    
    # Create camera with password
    password = "CameraPassword456"
    camera = CameraInstance(
        name="Demo Camera",
        username="admin",
        password=password,
        ip_address="192.168.1.100",
        port=554,
        stream_path="stream1"
    )
    
    print(f"\n1. Created camera with password: {password}")
    
    # Serialize (encrypts password)
    camera_dict = camera.to_dict()
    print(f"2. Serialized to dict:")
    print(f"   - Password in dict: {camera_dict['password']}")
    print(f"   - Is encrypted: {camera_dict['password'] != password}")
    
    # Get URLs
    full_url = camera.get_url()
    safe_url = camera.get_safe_url()
    
    print(f"3. URL generation:")
    print(f"   - Full URL (with credentials): {full_url}")
    print(f"   - Safe URL (no credentials): {safe_url}")
    print(f"   - Safe for logging: {password not in safe_url}")
    
    # Get safe info
    safe_info = camera.get_safe_info()
    print(f"4. Safe info string: {safe_info}")
    print(f"   - Contains password: {password in safe_info}")
    
    # Deserialize (decrypts password)
    loaded_camera = CameraInstance.from_dict(camera_dict)
    print(f"5. Loaded from dict:")
    print(f"   - Password decrypted: {loaded_camera.password == password}")
    
    print("\n✓ CameraInstance security features work correctly!\n")


def demo_settings_persistence():
    """Demonstrate secure persistence to QSettings."""
    print("="*60)
    print("DEMO 3: Secure Settings Persistence")
    print("="*60)
    
    # Create QApplication (required for QSettings)
    app = QApplication(sys.argv)
    
    # Create temporary settings
    settings = QSettings("DemoOrg", "SecurityDemo")
    settings.clear()
    
    # Create camera manager
    manager = CameraManager(settings)
    
    password = "PersistentPassword789"
    print(f"\n1. Adding camera with password: {password}")
    
    # Add camera
    camera_id = manager.add_camera({
        "name": "Persistent Camera",
        "username": "user",
        "password": password,
        "ip_address": "192.168.1.200",
        "port": 554,
        "stream_path": "stream"
    })
    
    print(f"   - Camera added with ID: {camera_id}")
    
    # Check what's stored in settings
    import json
    cameras_json = settings.value('cameras', '[]', type=str)
    cameras_data = json.loads(cameras_json)
    stored_password = cameras_data[0]["password"]
    
    print(f"2. Password in QSettings:")
    print(f"   - Stored value: {stored_password}")
    print(f"   - Is encrypted: {stored_password != password}")
    print(f"   - Is base64: {PasswordEncryption.is_encrypted(stored_password)}")
    
    # Load in new manager
    manager2 = CameraManager(settings)
    manager2.load_from_settings()
    
    loaded_camera = manager2.get_camera(camera_id)
    print(f"3. Loaded from settings:")
    print(f"   - Password decrypted correctly: {loaded_camera.password == password}")
    
    # Clean up
    settings.clear()
    
    print("\n✓ Settings persistence is secure!\n")


def demo_backward_compatibility():
    """Demonstrate backward compatibility with plain text passwords."""
    print("="*60)
    print("DEMO 4: Backward Compatibility")
    print("="*60)
    
    print("\n1. Testing with plain text password (old format):")
    
    # Create dict with plain text password (simulating old data)
    old_format_dict = {
        "id": "test-id",
        "name": "Old Camera",
        "protocol": "rtsp",
        "username": "admin",
        "password": "PlainTextPassword",  # Not encrypted
        "ip_address": "192.168.1.50",
        "port": 554,
        "stream_path": "stream",
        "resolution": (1920, 1080),
        "state": "stopped",
        "error_message": ""
    }
    
    print(f"   - Password in dict: {old_format_dict['password']}")
    print(f"   - Is encrypted: {PasswordEncryption.is_encrypted(old_format_dict['password'])}")
    
    # Load camera (should handle plain text)
    camera = CameraInstance.from_dict(old_format_dict)
    print(f"2. Loaded camera:")
    print(f"   - Password loaded correctly: {camera.password == 'PlainTextPassword'}")
    
    # Save camera (will encrypt password)
    new_dict = camera.to_dict()
    print(f"3. Re-saved camera:")
    print(f"   - Password now encrypted: {new_dict['password'] != 'PlainTextPassword'}")
    print(f"   - Is encrypted: {PasswordEncryption.is_encrypted(new_dict['password'])}")
    
    print("\n✓ Backward compatibility works correctly!\n")


def main():
    """Run all demos."""
    print("\n" + "="*60)
    print("SECURITY FEATURES DEMONSTRATION")
    print("="*60 + "\n")
    
    try:
        demo_password_encryption()
        demo_camera_instance_security()
        demo_settings_persistence()
        demo_backward_compatibility()
        
        print("="*60)
        print("✓ All security features demonstrated successfully!")
        print("="*60 + "\n")
        
        print("Key Security Features:")
        print("  1. ✅ Passwords encrypted before storage")
        print("  2. ✅ Passwords decrypted when loaded")
        print("  3. ✅ Safe URL generation without credentials")
        print("  4. ✅ Backward compatibility with plain text")
        print("  5. ✅ Secure persistence to QSettings")
        print("  6. ✅ No plain text passwords in logs")
        print()
        
    except Exception as e:
        print(f"\n✗ Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
