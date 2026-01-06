#!/usr/bin/env python3
"""
Simple test script to verify that show_offline_image() displays the offline image.
"""

import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ip_camera_player import CameraPanel, CameraInstance

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Test Offline Image Display")
        self.setGeometry(100, 100, 800, 600)
        
        # Create main widget
        main_widget = QWidget()
        layout = QVBoxLayout()
        
        # Create a camera instance
        camera = CameraInstance(
            camera_id="test-camera-1",
            name="Test Camera",
            ip_address="192.168.1.100",
            port=554,
            stream_path="stream1"
        )
        
        # Create camera panel
        self.panel = CameraPanel(camera)
        layout.addWidget(self.panel)
        
        # Add button to test showing offline image
        button = QPushButton("Show Offline Image")
        button.clicked.connect(self.show_offline)
        layout.addWidget(button)
        
        main_widget.setLayout(layout)
        self.setCentralWidget(main_widget)
    
    def show_offline(self):
        """Test showing the offline image"""
        print("Testing show_offline_image()...")
        self.panel.show_offline_image()
        print("Offline image should be visible now")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec_())
