#!/usr/bin/env python3
"""
Test script for multi-camera integration in MainWindow.

This script tests the basic functionality of the multi-camera support
including camera manager initialization, panel creation, and signal connections.
"""

import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QSettings
from ip_camera_player import Windows, CameraManager, migrate_settings


def test_main_window_initialization():
    """Test that MainWindow initializes correctly with multi-camera support."""
    app = QApplication(sys.argv)
    
    # Create main window
    window = Windows()
    
    # Verify camera manager exists
    assert hasattr(window, 'camera_manager'), "MainWindow should have camera_manager"
    assert isinstance(window.camera_manager, CameraManager), "camera_manager should be CameraManager instance"
    
    # Verify camera grid layout exists
    assert hasattr(window, 'camera_grid_layout'), "MainWindow should have camera_grid_layout"
    assert hasattr(window, 'camera_grid_container'), "MainWindow should have camera_grid_container"
    
    # Verify camera panels dictionary exists
    assert hasattr(window, 'camera_panels'), "MainWindow should have camera_panels dictionary"
    assert isinstance(window.camera_panels, dict), "camera_panels should be a dictionary"
    
    print("✓ MainWindow initialization test passed")
    
    return window


def test_camera_manager_integration():
    """Test that CameraManager is properly integrated."""
    app = QApplication(sys.argv)
    window = Windows()
    
    # Test adding a camera
    camera_config = {
        "name": "Test Camera",
        "protocol": "rtsp",
        "username": "admin",
        "password": "password",
        "ip_address": "192.168.1.100",
        "port": 554,
        "stream_path": "stream1",
        "resolution": (1920, 1080)
    }
    
    camera_id = window.camera_manager.add_camera(camera_config)
    assert camera_id is not None, "Camera should be added successfully"
    
    # Verify camera was added
    cameras = window.camera_manager.get_all_cameras()
    assert len(cameras) > 0, "Camera list should not be empty"
    
    # Verify panel was created
    assert camera_id in window.camera_panels, "Camera panel should be created"
    
    print("✓ CameraManager integration test passed")
    
    return window


def test_camera_selection():
    """Test camera selection functionality."""
    app = QApplication(sys.argv)
    window = Windows()
    
    # Add a test camera
    camera_config = {
        "name": "Test Camera",
        "protocol": "rtsp",
        "username": "admin",
        "password": "password",
        "ip_address": "192.168.1.100",
        "port": 554,
        "stream_path": "stream1",
        "resolution": (1920, 1080)
    }
    
    camera_id = window.camera_manager.add_camera(camera_config)
    
    # Select the camera
    window.handle_camera_selection(camera_id)
    
    # Verify selection
    selected = window.camera_manager.get_selected_camera()
    assert selected is not None, "A camera should be selected"
    assert selected.id == camera_id, "Selected camera should match"
    
    # Verify panel is marked as selected
    panel = window.camera_panels[camera_id]
    assert panel.is_selected, "Panel should be marked as selected"
    
    print("✓ Camera selection test passed")
    
    return window


def test_settings_migration():
    """Test settings migration from old format to new format."""
    # Create a temporary settings object with old format
    settings = QSettings('IP Camera Player Test', 'MigrationTest')
    
    # Clear any existing settings
    settings.clear()
    
    # Set old format settings
    settings.setValue('protocol', 'rtsp')
    settings.setValue('user', 'admin')
    settings.setValue('password', 'test123')
    settings.setValue('ip', '192.168.1.50')
    settings.setValue('port', 554)
    settings.setValue('stream_path', 'stream1')
    settings.setValue('video_resolution', '(1920, 1080)')
    
    # Run migration
    migrate_settings(settings)
    
    # Verify new format exists
    assert settings.contains('cameras'), "New format should have 'cameras' key"
    assert settings.contains('selected_camera_id'), "New format should have 'selected_camera_id' key"
    
    # Verify old keys are removed
    assert not settings.contains('ip'), "Old 'ip' key should be removed"
    
    print("✓ Settings migration test passed")
    
    # Clean up
    settings.clear()


def test_control_buttons_state():
    """Test that control buttons are properly enabled/disabled based on selection."""
    app = QApplication(sys.argv)
    
    # Clear any existing settings to start fresh
    settings = QSettings('IP Camera Player', 'AppSettings')
    settings.clear()
    
    window = Windows()
    
    # Initially, no camera selected - buttons should be disabled
    window.update_control_buttons()
    
    assert not window.start_button.isEnabled(), "Start button should be disabled with no selection"
    assert not window.stop_button.isEnabled(), "Stop button should be disabled with no selection"
    
    # Add and select a camera
    camera_config = {
        "name": "Test Camera",
        "protocol": "rtsp",
        "username": "admin",
        "password": "password",
        "ip_address": "192.168.1.100",
        "port": 554,
        "stream_path": "stream1",
        "resolution": (1920, 1080)
    }
    
    camera_id = window.camera_manager.add_camera(camera_config)
    window.handle_camera_selection(camera_id)
    
    # With stopped camera selected, start button should be enabled
    assert window.start_button.isEnabled(), "Start button should be enabled with stopped camera selected"
    assert not window.stop_button.isEnabled(), "Stop button should be disabled with stopped camera"
    
    print("✓ Control buttons state test passed")
    
    return window


def main():
    """Run all tests."""
    print("Running multi-camera integration tests...\n")
    
    try:
        test_settings_migration()
        test_main_window_initialization()
        test_camera_manager_integration()
        test_camera_selection()
        test_control_buttons_state()
        
        print("\n✅ All tests passed!")
        return 0
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
