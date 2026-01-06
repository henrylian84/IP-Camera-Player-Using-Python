"""
Test script for camera configuration UI components.

This script tests the CameraConfigDialog and CameraListWidget
to ensure they work correctly with the CameraManager.
"""

import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QSettings
from ip_camera_player import CameraManager, CameraListWidget, CameraConfigDialog


def test_camera_config_dialog():
    """Test CameraConfigDialog in add mode."""
    print("Testing CameraConfigDialog...")
    
    app = QApplication(sys.argv)
    
    # Test add mode
    dialog = CameraConfigDialog()
    
    # Verify initial state
    assert dialog.name_line_edit.text() == ""
    assert dialog.protocol_combo_box.currentText() == "rtsp"
    assert dialog.port_line_edit.text() == "554"
    
    # Test validation with empty fields
    is_valid, error = dialog.validate()
    assert not is_valid
    assert "name" in error.lower()
    
    # Fill in required fields
    dialog.name_line_edit.setText("Test Camera")
    dialog.ip_address_line_edit.setText("192.168.1.100")
    
    # Test validation with valid data
    is_valid, error = dialog.validate()
    assert is_valid
    assert error == ""
    
    # Test get_camera_data
    data = dialog.get_camera_data()
    assert data["name"] == "Test Camera"
    assert data["ip_address"] == "192.168.1.100"
    assert data["port"] == 554
    assert data["protocol"] == "rtsp"
    assert data["resolution"] == (1920, 1080)
    
    print("✓ CameraConfigDialog tests passed")


def test_camera_list_widget():
    """Test CameraListWidget with CameraManager."""
    print("Testing CameraListWidget...")
    
    app = QApplication(sys.argv)
    
    # Create settings and camera manager
    settings = QSettings('TestOrg', 'TestApp')
    settings.clear()  # Clear any existing settings
    
    camera_manager = CameraManager(settings)
    
    # Add some test cameras
    camera_manager.add_camera({
        "name": "Front Door",
        "ip_address": "192.168.1.100",
        "protocol": "rtsp",
        "username": "admin",
        "password": "password",
        "port": 554,
        "stream_path": "stream1",
        "resolution": (1920, 1080)
    })
    
    camera_manager.add_camera({
        "name": "Back Yard",
        "ip_address": "192.168.1.101",
        "protocol": "rtsp",
        "username": "admin",
        "password": "password",
        "port": 554,
        "stream_path": "stream1",
        "resolution": (1280, 720)
    })
    
    # Create list widget
    list_widget = CameraListWidget(camera_manager)
    
    # Verify cameras are displayed
    assert list_widget.camera_list_view.count() == 2
    
    # Verify buttons are initially disabled (no selection)
    assert not list_widget.edit_button.isEnabled()
    assert not list_widget.delete_button.isEnabled()
    
    # Select first item
    list_widget.camera_list_view.setCurrentRow(0)
    
    # Verify buttons are now enabled
    assert list_widget.edit_button.isEnabled()
    assert list_widget.delete_button.isEnabled()
    
    print("✓ CameraListWidget tests passed")


def test_integration():
    """Test integration between components."""
    print("Testing integration...")
    
    app = QApplication(sys.argv)
    
    # Create settings and camera manager
    settings = QSettings('TestOrg', 'TestApp')
    settings.clear()
    
    camera_manager = CameraManager(settings)
    
    # Add a camera
    camera_id = camera_manager.add_camera({
        "name": "Test Camera",
        "ip_address": "192.168.1.100",
        "protocol": "rtsp",
        "username": "admin",
        "password": "password",
        "port": 554,
        "stream_path": "stream1",
        "resolution": (1920, 1080)
    })
    
    assert camera_id is not None
    
    # Verify camera was added
    camera = camera_manager.get_camera(camera_id)
    assert camera is not None
    assert camera.name == "Test Camera"
    assert camera.ip_address == "192.168.1.100"
    
    # Test persistence
    camera_manager.save_to_settings()
    
    # Create new manager and load
    camera_manager2 = CameraManager(settings)
    camera_manager2.load_from_settings()
    
    # Verify camera was loaded
    cameras = camera_manager2.get_all_cameras()
    assert len(cameras) == 1
    assert cameras[0].name == "Test Camera"
    
    print("✓ Integration tests passed")


if __name__ == '__main__':
    try:
        test_camera_config_dialog()
        test_camera_list_widget()
        test_integration()
        print("\n✅ All tests passed!")
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
