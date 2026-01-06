"""
Test script for error handling functionality in multi-camera display.

This script tests:
1. Per-camera error display
2. Retry functionality
3. Configuration validation
4. Connection timeout handling
5. Storage error handling
"""

import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QSettings
from ip_camera_player import (
    CameraInstance, CameraManager, CameraPanel, CameraConfigDialog,
    CameraState
)


def test_camera_instance_timeout():
    """Test that CameraInstance properly stores connection timeout."""
    print("Testing CameraInstance timeout configuration...")
    
    # Create camera with custom timeout
    camera = CameraInstance(
        name="Test Camera",
        ip_address="192.168.1.100",
        connection_timeout=30
    )
    
    assert camera.connection_timeout == 30, "Timeout not set correctly"
    
    # Test serialization
    data = camera.to_dict()
    assert data["connection_timeout"] == 30, "Timeout not serialized"
    
    # Test deserialization
    camera2 = CameraInstance.from_dict(data)
    assert camera2.connection_timeout == 30, "Timeout not deserialized"
    
    print("✓ CameraInstance timeout configuration works correctly")


def test_camera_manager_storage_error_handling():
    """Test that CameraManager handles storage errors gracefully."""
    print("\nTesting CameraManager storage error handling...")
    
    # Create a temporary settings object
    settings = QSettings("TestOrg", "TestApp")
    settings.clear()
    
    manager = CameraManager(settings)
    
    # Test adding a camera
    camera_id = manager.add_camera({
        "name": "Test Camera",
        "ip_address": "192.168.1.100",
        "port": 554
    })
    
    assert camera_id is not None, "Failed to add camera"
    assert len(manager.get_all_cameras()) == 1, "Camera not added to list"
    
    # Test loading from settings
    manager2 = CameraManager(settings)
    success = manager2.load_from_settings()
    
    assert success, "Failed to load from settings"
    assert len(manager2.get_all_cameras()) == 1, "Camera not loaded"
    
    # Test with corrupted data
    settings.setValue('cameras', 'invalid json')
    manager3 = CameraManager(settings)
    success = manager3.load_from_settings()
    
    assert not success, "Should return False for corrupted data"
    assert len(manager3.get_all_cameras()) == 0, "Should fallback to empty list"
    
    # Cleanup
    settings.clear()
    
    print("✓ CameraManager storage error handling works correctly")


def test_config_validation():
    """Test configuration validation in CameraConfigDialog."""
    print("\nTesting configuration validation...")
    
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    dialog = CameraConfigDialog()
    
    # Test empty name validation
    dialog.name_line_edit.setText("")
    dialog.ip_address_line_edit.setText("192.168.1.100")
    is_valid, error = dialog.validate()
    assert not is_valid, "Should reject empty name"
    assert "name" in error.lower(), "Error message should mention name"
    
    # Test empty IP validation
    dialog.name_line_edit.setText("Test Camera")
    dialog.ip_address_line_edit.setText("")
    is_valid, error = dialog.validate()
    assert not is_valid, "Should reject empty IP"
    assert "ip" in error.lower(), "Error message should mention IP"
    
    # Test invalid IP format
    dialog.ip_address_line_edit.setText("999.999.999.999")
    is_valid, error = dialog.validate()
    assert not is_valid, "Should reject invalid IP"
    
    # Test invalid port
    dialog.ip_address_line_edit.setText("192.168.1.100")
    dialog.port_line_edit.setText("99999")
    is_valid, error = dialog.validate()
    assert not is_valid, "Should reject invalid port"
    assert "port" in error.lower(), "Error message should mention port"
    
    # Test valid configuration
    dialog.port_line_edit.setText("554")
    is_valid, error = dialog.validate()
    assert is_valid, f"Should accept valid config, but got error: {error}"
    
    print("✓ Configuration validation works correctly")


def test_camera_panel_error_display():
    """Test that CameraPanel displays errors correctly."""
    print("\nTesting CameraPanel error display...")
    
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    camera = CameraInstance(
        name="Test Camera",
        ip_address="192.168.1.100"
    )
    
    panel = CameraPanel(camera)
    
    # Give the panel a size and show it (required for child widgets to be visible)
    panel.resize(640, 480)
    panel.show()
    
    # Test showing error
    panel.set_error("Connection failed: timeout")
    assert panel.error_container.isVisible(), "Error container should be visible"
    assert "timeout" in panel.error_label.text().lower(), "Error message should be displayed"
    assert panel.retry_button.isVisible(), "Retry button should be visible"
    
    # Test clearing error
    panel.set_error("")
    assert not panel.error_container.isVisible(), "Error container should be hidden"
    
    print("✓ CameraPanel error display works correctly")


def run_all_tests():
    """Run all error handling tests."""
    print("=" * 60)
    print("Running Error Handling Tests")
    print("=" * 60)
    
    try:
        test_camera_instance_timeout()
        test_camera_manager_storage_error_handling()
        test_config_validation()
        test_camera_panel_error_display()
        
        print("\n" + "=" * 60)
        print("All tests passed! ✓")
        print("=" * 60)
        return True
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        return False
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
