"""
Demo script for TopNavigationBar component.

This script demonstrates the TopNavigationBar widget with branding,
menu buttons, and status indicators.
"""

import sys
import os

# Add parent directory to path to import from ip_camera_player
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel
from PyQt5.QtCore import Qt
from ip_camera_player import TopNavigationBar


class DemoWindow(QMainWindow):
    """Demo window to showcase TopNavigationBar."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TopNavigationBar Demo")
        self.setMinimumSize(800, 600)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create layout
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create TopNavigationBar
        self.top_nav = TopNavigationBar(self)
        
        # Set branding
        logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                 "images", "Security-Camera-icon.png")
        self.top_nav.set_branding(logo_path, "IP Camera Player")
        
        # Add menu buttons
        self.top_nav.add_menu_button("Settings", self.on_settings_clicked)
        self.top_nav.add_menu_button("View", self.on_view_clicked)
        self.top_nav.add_menu_button("Help", self.on_help_clicked)
        
        # Add status indicators
        camera_count_label = QLabel("Cameras: 0")
        self.top_nav.add_status_indicator("camera_count", camera_count_label)
        
        status_label = QLabel("Status: Ready")
        self.top_nav.add_status_indicator("status", status_label)
        
        # Connect signal
        self.top_nav.menu_clicked.connect(self.on_menu_clicked)
        
        # Add to layout
        layout.addWidget(self.top_nav)
        
        # Add content area
        content_label = QLabel("Content Area\n\nClick menu buttons to test functionality")
        content_label.setAlignment(Qt.AlignCenter)
        content_label.setStyleSheet("""
            QLabel {
                background-color: #1E1E1E;
                color: white;
                font-size: 18px;
                padding: 20px;
            }
        """)
        layout.addWidget(content_label)
        
        # Apply dark theme to window
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1E1E1E;
            }
        """)
    
    def on_settings_clicked(self):
        """Handle Settings button click."""
        print("Settings button clicked")
        self.top_nav.update_status("status", "Status: Settings opened")
    
    def on_view_clicked(self):
        """Handle View button click."""
        print("View button clicked")
        self.top_nav.update_status("status", "Status: View changed")
    
    def on_help_clicked(self):
        """Handle Help button click."""
        print("Help button clicked")
        self.top_nav.update_status("status", "Status: Help opened")
    
    def on_menu_clicked(self, menu_name):
        """Handle menu_clicked signal."""
        print(f"Menu clicked signal received: {menu_name}")


def main():
    """Run the demo application."""
    app = QApplication(sys.argv)
    window = DemoWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
