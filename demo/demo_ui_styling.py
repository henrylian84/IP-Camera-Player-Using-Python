"""
Demo script to showcase the UI styling improvements for task 9.

This script demonstrates:
- Camera panel selection border styling
- Camera panel error display styling
- Camera list widget styling
- Status bar multi-camera updates
"""

import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QHBoxLayout
from PyQt5.QtCore import QSettings, QTimer
from ip_camera_player import (
    CameraPanel, CameraInstance, CameraManager, CameraListWidget,
    CameraState
)


class StylingDemo(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("UI Styling Demo - Task 9")
        self.setGeometry(100, 100, 1200, 700)
        
        # Create settings and camera manager
        self.settings = QSettings('CameraPlayerDemo', 'UIStyling')
        self.camera_manager = CameraManager(self.settings)
        
        # Create sample cameras
        self.create_sample_cameras()
        
        # Create main layout
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        
        # Create camera panels container
        panels_layout = QHBoxLayout()
        
        # Create three camera panels to demonstrate styling
        cameras = self.camera_manager.get_all_cameras()
        self.panels = []
        
        for i, camera in enumerate(cameras[:3]):
            panel = CameraPanel(camera)
            self.panels.append(panel)
            panels_layout.addWidget(panel)
            
            # Connect click signal
            panel.clicked.connect(self.on_panel_clicked)
        
        main_layout.addLayout(panels_layout)
        
        # Create control buttons
        controls_layout = QHBoxLayout()
        
        btn_select_1 = QPushButton("Select Camera 1")
        btn_select_1.clicked.connect(lambda: self.select_camera(0))
        controls_layout.addWidget(btn_select_1)
        
        btn_select_2 = QPushButton("Select Camera 2")
        btn_select_2.clicked.connect(lambda: self.select_camera(1))
        controls_layout.addWidget(btn_select_2)
        
        btn_select_3 = QPushButton("Select Camera 3")
        btn_select_3.clicked.connect(lambda: self.select_camera(2))
        controls_layout.addWidget(btn_select_3)
        
        btn_show_error = QPushButton("Show Error on Selected")
        btn_show_error.clicked.connect(self.show_error_on_selected)
        controls_layout.addWidget(btn_show_error)
        
        btn_show_loading = QPushButton("Show Loading on Selected")
        btn_show_loading.clicked.connect(self.show_loading_on_selected)
        controls_layout.addWidget(btn_show_loading)
        
        btn_open_list = QPushButton("Open Camera List")
        btn_open_list.clicked.connect(self.open_camera_list)
        controls_layout.addWidget(btn_open_list)
        
        main_layout.addLayout(controls_layout)
        
        # Add info label
        from PyQt5.QtWidgets import QLabel
        info_label = QLabel(
            "Demo Features:\n"
            "• Selection Border: Click cameras to see bright cyan-blue 4px border\n"
            "• Error Display: Click 'Show Error' to see styled error with icon and retry button\n"
            "• Camera List: Click 'Open Camera List' to see styled list with state icons\n"
            "• Status Bar: Shows camera count and selected camera info"
        )
        info_label.setStyleSheet("padding: 10px; background-color: #F0F0F0; border-radius: 5px;")
        main_layout.addWidget(info_label)
        
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        
        # Create status bar
        self.statusBar().showMessage("Ready - 3 cameras configured")
        
        print("\n" + "="*60)
        print("UI STYLING DEMO - TASK 9")
        print("="*60)
        print("\nDemonstrating the following improvements:")
        print("\n1. Camera Panel Selection Border (Task 9.1):")
        print("   - Bright cyan-blue color (RGB: 0, 180, 255)")
        print("   - 4px width for better visibility")
        print("   - Proper offset to prevent clipping")
        print("\n2. Camera Panel Error Display (Task 9.2):")
        print("   - Warning icon (⚠) in gold color")
        print("   - Improved error message styling")
        print("   - Styled retry button with hover effects")
        print("   - Better container appearance with border")
        print("\n3. Camera List Widget (Task 9.3):")
        print("   - Styled list items with state icons")
        print("   - Consistent button styling")
        print("   - Delete button in red for destructive action")
        print("   - Improved spacing and padding")
        print("\n4. Status Bar Multi-Camera (Task 9.4):")
        print("   - Shows camera count")
        print("   - Displays selected camera info")
        print("   - Shows camera state in status")
        print("\nTry the buttons to see the styling in action!")
        print("="*60 + "\n")
    
    def create_sample_cameras(self):
        """Create sample cameras for demonstration."""
        cameras_data = [
            {
                "name": "Front Door Camera",
                "ip_address": "192.168.1.100",
                "protocol": "rtsp",
                "username": "admin",
                "password": "password123",
                "port": 554,
                "stream_path": "stream1",
                "resolution": (1920, 1080)
            },
            {
                "name": "Back Yard Camera",
                "ip_address": "192.168.1.101",
                "protocol": "rtsp",
                "username": "admin",
                "password": "password123",
                "port": 554,
                "stream_path": "stream1",
                "resolution": (1280, 720)
            },
            {
                "name": "Garage Camera",
                "ip_address": "192.168.1.102",
                "protocol": "rtsp",
                "username": "admin",
                "password": "password123",
                "port": 554,
                "stream_path": "stream1",
                "resolution": (640, 480)
            }
        ]
        
        for data in cameras_data:
            self.camera_manager.add_camera(data)
    
    def select_camera(self, index):
        """Select a camera by index."""
        if index < len(self.panels):
            panel = self.panels[index]
            camera_id = panel.camera_instance.id
            
            # Update selection visually
            for i, p in enumerate(self.panels):
                p.set_selected(i == index)
            
            # Update camera manager
            self.camera_manager.select_camera(camera_id)
            
            # Update status bar
            camera = panel.camera_instance
            self.statusBar().showMessage(
                f"Selected: {camera.name} ({camera.state.value.capitalize()}) | "
                f"Cameras: {len(self.camera_manager.get_all_cameras())}"
            )
            
            print(f"✓ Selected camera {index + 1}: {camera.name}")
            print(f"  Selection border should be visible (bright cyan-blue, 4px)")
    
    def on_panel_clicked(self, camera_id):
        """Handle panel click."""
        for i, panel in enumerate(self.panels):
            if panel.camera_instance.id == camera_id:
                self.select_camera(i)
                break
    
    def show_error_on_selected(self):
        """Show error on the selected camera panel."""
        selected = self.camera_manager.get_selected_camera()
        if selected:
            for panel in self.panels:
                if panel.camera_instance.id == selected.id:
                    panel.set_error(
                        "Connection failed: Unable to reach camera at "
                        f"{selected.ip_address}. Please check network connection "
                        "and camera settings."
                    )
                    print(f"✓ Showing styled error on {selected.name}")
                    print("  Error display features:")
                    print("  - Warning icon (⚠) in gold")
                    print("  - Styled error message")
                    print("  - Blue retry button with hover effects")
                    break
        else:
            print("! No camera selected. Select a camera first.")
    
    def show_loading_on_selected(self):
        """Show loading animation on the selected camera panel."""
        selected = self.camera_manager.get_selected_camera()
        if selected:
            for panel in self.panels:
                if panel.camera_instance.id == selected.id:
                    panel.set_loading(True)
                    panel.set_error("")  # Clear any error
                    print(f"✓ Showing loading animation on {selected.name}")
                    
                    # Auto-hide after 2 seconds
                    QTimer.singleShot(2000, lambda: panel.set_loading(False))
                    break
        else:
            print("! No camera selected. Select a camera first.")
    
    def open_camera_list(self):
        """Open the camera list widget to demonstrate styling."""
        print("\n✓ Opening Camera List Widget")
        print("  Features to observe:")
        print("  - State icons for each camera (⏹ = stopped)")
        print("  - Styled list items with hover effects")
        print("  - Consistent button styling")
        print("  - Delete button in red")
        print("  - Improved spacing and layout")
        
        list_widget = CameraListWidget(self.camera_manager, self)
        list_widget.exec_()


def main():
    """Main entry point for the demo."""
    app = QApplication(sys.argv)
    demo = StylingDemo()
    demo.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
