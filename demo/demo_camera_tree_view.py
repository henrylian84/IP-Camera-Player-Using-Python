"""
Demo script for CameraTreeView component.

This script demonstrates the CameraTreeView widget with sample cameras
organized by location.
"""

import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QHBoxLayout
from PyQt5.QtCore import QSettings

# Import components
from ip_camera_player import CameraTreeView, CameraManager, CameraState


class CameraTreeViewDemo(QMainWindow):
    """Demo window for CameraTreeView."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CameraTreeView Demo")
        self.setGeometry(100, 100, 400, 600)
        
        # Create settings and camera manager
        self.settings = QSettings('CameraTreeViewDemo', 'Demo')
        self.camera_manager = CameraManager(self.settings)
        
        # Add sample cameras
        self._add_sample_cameras()
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create layout
        layout = QVBoxLayout(central_widget)
        
        # Create tree view
        self.tree_view = CameraTreeView(self.camera_manager)
        self.tree_view.refresh_tree()
        
        # Connect signals
        self.tree_view.camera_selected.connect(self._on_camera_selected)
        self.tree_view.camera_double_clicked.connect(self._on_camera_double_clicked)
        
        # Add tree view to layout
        layout.addWidget(self.tree_view)
        
        # Create button panel
        button_layout = QHBoxLayout()
        
        # Add buttons
        refresh_btn = QPushButton("Refresh Tree")
        refresh_btn.clicked.connect(self.tree_view.refresh_tree)
        button_layout.addWidget(refresh_btn)
        
        add_camera_btn = QPushButton("Add Camera")
        add_camera_btn.clicked.connect(self._add_random_camera)
        button_layout.addWidget(add_camera_btn)
        
        toggle_state_btn = QPushButton("Toggle State")
        toggle_state_btn.clicked.connect(self._toggle_camera_state)
        button_layout.addWidget(toggle_state_btn)
        
        layout.addLayout(button_layout)
        
        # Status label
        from PyQt5.QtWidgets import QLabel
        self.status_label = QLabel("Select a camera to see its ID")
        self.status_label.setStyleSheet("padding: 10px; background-color: #2D2D2D; color: white;")
        layout.addWidget(self.status_label)
    
    def _add_sample_cameras(self):
        """Add sample cameras to the manager."""
        # Office cameras
        self.camera_manager.add_camera({
            "name": "Office Front Door",
            "ip_address": "192.168.1.100",
            "port": 554
        })
        
        self.camera_manager.add_camera({
            "name": "Office Lobby",
            "ip_address": "192.168.1.101",
            "port": 554
        })
        
        # Warehouse cameras
        self.camera_manager.add_camera({
            "name": "Warehouse Entrance",
            "ip_address": "192.168.1.110",
            "port": 554
        })
        
        self.camera_manager.add_camera({
            "name": "Warehouse Loading Dock",
            "ip_address": "192.168.1.111",
            "port": 554
        })
        
        # Parking cameras
        self.camera_manager.add_camera({
            "name": "Parking Lot North",
            "ip_address": "192.168.1.120",
            "port": 554
        })
        
        self.camera_manager.add_camera({
            "name": "Parking Lot South",
            "ip_address": "192.168.1.121",
            "port": 554
        })
        
        # Set some cameras to different states for visual variety
        cameras = self.camera_manager.get_all_cameras()
        if len(cameras) >= 3:
            cameras[1].state = CameraState.RUNNING
            cameras[2].state = CameraState.ERROR
            cameras[2].error_message = "Connection timeout"
    
    def _add_random_camera(self):
        """Add a random camera for testing."""
        import random
        num = random.randint(1000, 9999)
        self.camera_manager.add_camera({
            "name": f"Camera {num}",
            "ip_address": f"192.168.1.{random.randint(1, 254)}",
            "port": 554
        })
        self.tree_view.refresh_tree()
        self.status_label.setText(f"Added Camera {num}")
    
    def _toggle_camera_state(self):
        """Toggle the state of the selected camera."""
        camera_id = self.tree_view.get_selected_camera_id()
        if not camera_id:
            self.status_label.setText("No camera selected")
            return
        
        camera = self.camera_manager.get_camera(camera_id)
        if not camera:
            return
        
        # Cycle through states
        states = [CameraState.STOPPED, CameraState.STARTING, CameraState.RUNNING, 
                  CameraState.PAUSED, CameraState.ERROR]
        current_index = states.index(camera.state)
        next_index = (current_index + 1) % len(states)
        camera.state = states[next_index]
        
        if camera.state == CameraState.ERROR:
            camera.error_message = "Test error"
        
        # Update display
        self.tree_view.update_camera_state(camera_id)
        self.status_label.setText(f"Camera state: {camera.state.value}")
    
    def _on_camera_selected(self, camera_id):
        """Handle camera selection."""
        camera = self.camera_manager.get_camera(camera_id)
        if camera:
            self.status_label.setText(f"Selected: {camera.name} (ID: {camera_id[:8]}...)")
    
    def _on_camera_double_clicked(self, camera_id):
        """Handle camera double-click."""
        camera = self.camera_manager.get_camera(camera_id)
        if camera:
            self.status_label.setText(f"Double-clicked: {camera.name} - Would open fullscreen")


def main():
    """Run the demo."""
    app = QApplication(sys.argv)
    
    # Apply dark theme to application
    app.setStyle('Fusion')
    app.setStyleSheet("""
        QMainWindow {
            background-color: #1E1E1E;
        }
        QPushButton {
            background-color: #2D2D2D;
            color: white;
            border: none;
            padding: 8px 16px;
            font-size: 12px;
        }
        QPushButton:hover {
            background-color: #3F3F3F;
        }
        QPushButton:pressed {
            background-color: #0078D7;
        }
    """)
    
    demo = CameraTreeViewDemo()
    demo.show()
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
