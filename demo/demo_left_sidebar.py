#!/usr/bin/env python3
"""
Demo script to showcase the LeftSidebar component.

This demo creates a simple window with the LeftSidebar to demonstrate
its collapse/expand functionality and styling.
"""

import sys
import os

# Add parent directory to path to import from ip_camera_player
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QLabel
from PyQt5.QtCore import Qt
from ip_camera_player import LeftSidebar


class DemoWindow(QMainWindow):
    """Demo window to showcase LeftSidebar."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LeftSidebar Demo")
        self.setGeometry(100, 100, 800, 600)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create LeftSidebar
        self.sidebar = LeftSidebar(self)
        
        # Connect to collapsed_changed signal
        self.sidebar.collapsed_changed.connect(self.on_sidebar_collapsed)
        
        # Create placeholder content area
        content_area = QWidget()
        content_area.setStyleSheet("background-color: #1E1E1E;")
        
        content_layout = QHBoxLayout(content_area)
        content_label = QLabel("Main Content Area\n\nClick the collapse button (◀/▶) on the sidebar to toggle it.")
        content_label.setAlignment(Qt.AlignCenter)
        content_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 16px;
                padding: 20px;
            }
        """)
        content_layout.addWidget(content_label)
        
        # Add widgets to main layout
        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(content_area, 1)  # Content area takes remaining space
        
        # Add a placeholder label to the sidebar tree container
        placeholder = QLabel("Camera Tree View\nwill be here", self.sidebar.tree_container)
        placeholder.setAlignment(Qt.AlignCenter)
        placeholder.setStyleSheet("""
            QLabel {
                color: #CCCCCC;
                font-size: 12px;
                padding: 20px;
            }
        """)
        self.sidebar.tree_layout.addWidget(placeholder)
        
        # Status label
        self.status_label = QLabel("Sidebar: Expanded")
        self.status_label.setStyleSheet("color: white; padding: 10px;")
        self.statusBar().addWidget(self.status_label)
    
    def on_sidebar_collapsed(self, is_collapsed):
        """Handle sidebar collapse state change."""
        state = "Collapsed" if is_collapsed else "Expanded"
        self.status_label.setText(f"Sidebar: {state}")
        print(f"Sidebar state changed: {state}")


def main():
    """Run the demo application."""
    app = QApplication(sys.argv)
    
    # Set application-wide dark theme
    app.setStyle("Fusion")
    
    window = DemoWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
