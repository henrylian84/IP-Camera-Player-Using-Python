"""
Demo script for camera configuration UI components.

This script demonstrates the CameraConfigDialog and CameraListWidget
in action, allowing manual testing of the UI.
"""

import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QSettings
from ip_camera_player import CameraManager, CameraListWidget


def main():
    """Main entry point for the demo."""
    app = QApplication(sys.argv)
    
    # Create settings and camera manager
    settings = QSettings('CameraPlayerDemo', 'CameraConfigUI')
    
    camera_manager = CameraManager(settings)
    camera_manager.load_from_settings()
    
    # If no cameras exist, add some sample ones
    if len(camera_manager.get_all_cameras()) == 0:
        print("Adding sample cameras...")
        camera_manager.add_camera({
            "name": "Front Door Camera",
            "ip_address": "192.168.1.100",
            "protocol": "rtsp",
            "username": "admin",
            "password": "password123",
            "port": 554,
            "stream_path": "stream1",
            "resolution": (1920, 1080)
        })
        
        camera_manager.add_camera({
            "name": "Back Yard Camera",
            "ip_address": "192.168.1.101",
            "protocol": "rtsp",
            "username": "admin",
            "password": "password123",
            "port": 554,
            "stream_path": "stream1",
            "resolution": (1280, 720)
        })
        
        camera_manager.add_camera({
            "name": "Garage Camera",
            "ip_address": "192.168.1.102",
            "protocol": "rtsp",
            "username": "admin",
            "password": "password123",
            "port": 554,
            "stream_path": "stream1",
            "resolution": (640, 480)
        })
    
    # Create and show the camera list widget
    list_widget = CameraListWidget(camera_manager)
    list_widget.show()
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
