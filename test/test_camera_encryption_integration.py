"""
Integration test for camera encryption with CameraInstance.

This script tests that passwords are properly encrypted when saving
and decrypted when loading camera configurations.
"""

import sys
import json
from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QApplication

# Import after creating QApplication to avoid Qt errors
app = QApplication(sys.argv)

from ip_camera_player import CameraInstance, CameraManager, migrate_settings
from camera_security import encrypt_password, decrypt_password


def test_camera_instance_serialization():
    """Test that CameraInstance properly encrypts passwords during serialization."""
    print("Testing CameraInstance password encryption...")
    
    # Create a camera with a password
    password = "MySecretPassword123"
    camera = CameraInstance(
        name="Test Camera",
        username="admin",
        password=password,
        ip_address="192.168.1.100",
        port=554,
        stream_path="stream1"
    )
    
    # Serialize to dict
    camera_dict = camera.to_dict()
    
    # Verify password is encrypted in the dict
    assert camera_dict["password"] != password, "Password should be encrypted in dict"
    assert camera_dict["password"] != "", "Encrypted password should not be empty"
    print(f"  ✓ Password encrypted in serialization")
    print(f"    Original: {password}")
    print(f"    Encrypted: {camera_dict['password'][:20]}...")
    
    # Verify we can decrypt it manually
    decrypted = decrypt_password(camera_dict["password"])
    assert decrypted == password, "Manual decryption should recover original password"
    print(f"  ✓ Manual decryption successful")
    
    # Deserialize from dict
    loaded_camera = CameraInstance.from_dict(camera_dict)
    
    # Verify password is decrypted correctly
    assert loaded_camera.password == password, "Password should be decrypted when loading"
    print(f"  ✓ Password decrypted correctly when loading")
    
    # Verify URL construction works with decrypted password
    url = loaded_camera.get_url()
    assert password in url, "URL should contain the decrypted password"
    print(f"  ✓ URL construction works with decrypted password")
    
    # Verify safe URL doesn't contain password
    safe_url = loaded_camera.get_safe_url()
    assert password not in safe_url, "Safe URL should not contain password"
    assert "admin" not in safe_url, "Safe URL should not contain username"
    print(f"  ✓ Safe URL doesn't contain credentials")
    
    print("✓ CameraInstance encryption integration tests passed\n")


def test_camera_manager_persistence():
    """Test that CameraManager properly persists encrypted passwords."""
    print("Testing CameraManager password persistence...")
    
    # Create a temporary settings object
    settings = QSettings("TestOrg", "TestApp_Security")
    settings.clear()  # Clear any existing data
    
    # Create camera manager
    manager = CameraManager(settings)
    
    # Add a camera with password
    password = "TestPassword456"
    camera_id = manager.add_camera({
        "name": "Persistent Camera",
        "username": "user",
        "password": password,
        "ip_address": "192.168.1.200",
        "port": 554,
        "stream_path": "stream"
    })
    
    assert camera_id is not None, "Camera should be added successfully"
    print(f"  ✓ Camera added with ID: {camera_id}")
    
    # Verify password is encrypted in settings
    cameras_json = settings.value('cameras', '[]', type=str)
    cameras_data = json.loads(cameras_json)
    
    assert len(cameras_data) == 1, "Should have one camera in settings"
    stored_password = cameras_data[0]["password"]
    
    assert stored_password != password, "Password should be encrypted in settings"
    assert stored_password != "", "Encrypted password should not be empty"
    print(f"  ✓ Password encrypted in QSettings")
    print(f"    Original: {password}")
    print(f"    Stored (encrypted): {stored_password[:20]}...")
    
    # Create a new manager and load from settings
    manager2 = CameraManager(settings)
    manager2.load_from_settings()
    
    # Verify camera was loaded
    cameras = manager2.get_all_cameras()
    assert len(cameras) == 1, "Should load one camera"
    
    loaded_camera = cameras[0]
    assert loaded_camera.password == password, "Password should be decrypted when loading"
    print(f"  ✓ Password decrypted correctly when loading from settings")
    
    # Clean up
    settings.clear()
    
    print("✓ CameraManager persistence tests passed\n")


def test_settings_migration():
    """Test that settings migration encrypts passwords."""
    print("Testing settings migration with encryption...")
    
    # Create a temporary settings object with old format
    settings = QSettings("TestOrg", "TestApp_Migration")
    settings.clear()
    
    # Set up old format settings
    old_password = "OldPassword789"
    settings.setValue('protocol', 'rtsp')
    settings.setValue('user', 'olduser')
    settings.setValue('password', old_password)  # Plain text in old format
    settings.setValue('ip', '192.168.1.50')
    settings.setValue('port', 554)
    settings.setValue('stream_path', 'oldstream')
    settings.setValue('video_resolution', '(1920, 1080)')
    
    print(f"  ✓ Old format settings created with plain text password")
    
    # Run migration
    migrate_settings(settings)
    
    # Verify new format exists
    assert settings.contains('cameras'), "Migration should create 'cameras' key"
    print(f"  ✓ Migration created new format")
    
    # Load and verify password is encrypted
    cameras_json = settings.value('cameras', '[]', type=str)
    cameras_data = json.loads(cameras_json)
    
    assert len(cameras_data) == 1, "Should have migrated one camera"
    migrated_password = cameras_data[0]["password"]
    
    assert migrated_password != old_password, "Migrated password should be encrypted"
    assert migrated_password != "", "Encrypted password should not be empty"
    print(f"  ✓ Password encrypted during migration")
    print(f"    Original: {old_password}")
    print(f"    Migrated (encrypted): {migrated_password[:20]}...")
    
    # Verify we can decrypt it
    decrypted = decrypt_password(migrated_password)
    assert decrypted == old_password, "Should be able to decrypt migrated password"
    print(f"  ✓ Migrated password can be decrypted")
    
    # Clean up
    settings.clear()
    
    print("✓ Settings migration tests passed\n")


def test_empty_password_handling():
    """Test handling of empty passwords."""
    print("Testing empty password handling...")
    
    # Create camera with empty password
    camera = CameraInstance(
        name="No Password Camera",
        username="user",
        password="",
        ip_address="192.168.1.100"
    )
    
    # Serialize
    camera_dict = camera.to_dict()
    assert camera_dict["password"] == "", "Empty password should remain empty"
    print(f"  ✓ Empty password remains empty after serialization")
    
    # Deserialize
    loaded_camera = CameraInstance.from_dict(camera_dict)
    assert loaded_camera.password == "", "Empty password should remain empty after loading"
    print(f"  ✓ Empty password remains empty after deserialization")
    
    # Verify URL construction works without password
    url = loaded_camera.get_url()
    assert "@" not in url, "URL should not contain @ when no credentials"
    print(f"  ✓ URL construction works without password")
    
    print("✓ Empty password handling tests passed\n")


def main():
    """Run all integration tests."""
    print("="*60)
    print("Running Camera Encryption Integration Tests")
    print("="*60 + "\n")
    
    try:
        test_camera_instance_serialization()
        test_camera_manager_persistence()
        test_settings_migration()
        test_empty_password_handling()
        
        print("="*60)
        print("✓ All integration tests passed!")
        print("="*60)
        return 0
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
