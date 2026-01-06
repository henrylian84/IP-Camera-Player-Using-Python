#!/usr/bin/env python3
"""
Demo script for multi-camera functionality.

This script demonstrates the multi-camera support in the IP Camera Player,
including adding multiple cameras, selecting cameras, and managing the grid layout.
"""

import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QSettings
from ip_camera_player import Windows


def setup_demo_cameras(window):
    """Add some demo cameras to the application."""
    demo_cameras = [
        {
            "name": "Front Door",
            "protocol": "rtsp",
            "username": "admin",
            "password": "password",
            "ip_address": "192.168.1.100",
            "port": 554,
            "stream_path": "stream1",
            "resolution": (1920, 1080)
        },
        {
            "name": "Back Yard",
            "protocol": "rtsp",
            "username": "admin",
            "password": "password",
            "ip_address": "192.168.1.101",
            "port": 554,
            "stream_path": "stream1",
            "resolution": (1920, 1080)
        },
        {
            "name": "Garage",
            "protocol": "rtsp",
            "username": "admin",
            "password": "password",
            "ip_address": "192.168.1.102",
            "port": 554,
            "stream_path": "stream1",
            "resolution": (1280, 720)
        },
        {
            "name": "Living Room",
            "protocol": "rtsp",
            "username": "admin",
            "password": "password",
            "ip_address": "192.168.1.103",
            "port": 554,
            "stream_path": "stream1",
            "resolution": (1280, 720)
        }
    ]
    
    print("Adding demo cameras...")
    for camera_config in demo_cameras:
        camera_id = window.camera_manager.add_camera(camera_config)
        print(f"  Added: {camera_config['name']} (ID: {camera_id})")
    
    # Select the first camera
    cameras = window.camera_manager.get_all_cameras()
    if cameras:
        window.handle_camera_selection(cameras[0].id)
        print(f"\nSelected camera: {cameras[0].name}")
    
    print(f"\nTotal cameras: {len(cameras)}")
    print("\nDemo cameras added successfully!")
    print("\nYou can now:")
    print("  - Click on a camera panel to select it")
    print("  - Double-click a camera panel to toggle fullscreen")
    print("  - Drag and drop camera panels to reorder them")
    print("  - Use the Settings button to add/edit/delete cameras")
    print("  - Use Start/Stop/Pause buttons to control the selected camera")
    print("  - Use Snapshot button to capture from the selected camera")


def main():
    """Run the demo application."""
    app = QApplication(sys.argv)
    
    # Optional: Clear existing settings to start fresh
    # Uncomment the next two lines if you want to start with a clean slate
    # settings = QSettings('IP Camera Player', 'AppSettings')
    # settings.clear()
    
    # Create main window
    window = Windows()
    
    # Check if cameras already exist
    existing_cameras = window.camera_manager.get_all_cameras()
    
    if len(existing_cameras) == 0:
        # No cameras exist, add demo cameras
        setup_demo_cameras(window)
    else:
        print(f"Found {len(existing_cameras)} existing cameras:")
        for camera in existing_cameras:
            print(f"  - {camera.name} ({camera.ip_address})")
        print("\nTo start fresh, uncomment the settings.clear() lines in the script.")
    
    # Show the window
    window.show()
    
    # Run the application
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
