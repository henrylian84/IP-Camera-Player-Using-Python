"""
Visual demonstration of CameraPanel functionality.
This creates a simple window showing a CameraPanel with test features.
"""
import sys
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QHBoxLayout
from PyQt5.QtCore import QTimer
from ip_camera_player import CameraPanel, CameraInstance

class CameraPanelDemo(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CameraPanel Demo")
        self.setGeometry(100, 100, 800, 600)
        
        # Create a camera instance
        self.camera = CameraInstance(
            name="Demo Camera",
            ip_address="192.168.1.100",
            port=554,
            username="admin",
            password="password",
            stream_path="stream1"
        )
        
        # Create camera panel
        self.panel = CameraPanel(self.camera)
        
        # Create control buttons
        self.btn_select = QPushButton("Toggle Selection")
        self.btn_select.clicked.connect(self.toggle_selection)
        
        self.btn_loading = QPushButton("Show Loading")
        self.btn_loading.clicked.connect(self.show_loading)
        
        self.btn_error = QPushButton("Show Error")
        self.btn_error.clicked.connect(self.show_error)
        
        self.btn_frame = QPushButton("Show Test Frame")
        self.btn_frame.clicked.connect(self.show_test_frame)
        
        self.btn_clear = QPushButton("Clear")
        self.btn_clear.clicked.connect(self.clear_panel)
        
        # Connect panel signals
        self.panel.clicked.connect(lambda cam_id: print(f"Panel clicked: {cam_id}"))
        self.panel.double_clicked.connect(lambda cam_id: print(f"Panel double-clicked: {cam_id}"))
        
        # Setup layout
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.btn_select)
        button_layout.addWidget(self.btn_loading)
        button_layout.addWidget(self.btn_error)
        button_layout.addWidget(self.btn_frame)
        button_layout.addWidget(self.btn_clear)
        
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.panel)
        main_layout.addLayout(button_layout)
        
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)
        
        print("CameraPanel Demo Started")
        print(f"Camera ID: {self.camera.id}")
        print(f"Camera Name: {self.camera.name}")
        print("\nTry the following:")
        print("- Click 'Toggle Selection' to see selection border")
        print("- Click 'Show Loading' to see loading animation")
        print("- Click 'Show Error' to see error message")
        print("- Click 'Show Test Frame' to display a test pattern")
        print("- Use mouse wheel to zoom in/out on the frame")
        print("- Click and drag to pan the frame")
        print("- Double-click the panel to test fullscreen signal")
    
    def toggle_selection(self):
        self.panel.set_selected(not self.panel.is_selected)
        print(f"Selection: {self.panel.is_selected}")
    
    def show_loading(self):
        self.panel.set_loading(True)
        print("Loading animation shown")
        
        # Auto-hide after 2 seconds
        QTimer.singleShot(2000, lambda: self.panel.set_loading(False))
    
    def show_error(self):
        self.panel.set_error("Connection failed: Unable to reach camera at 192.168.1.100")
        print("Error message shown")
    
    def show_test_frame(self):
        # Create a colorful test pattern
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Create colored rectangles
        frame[0:160, 0:213] = [255, 0, 0]      # Red
        frame[0:160, 213:426] = [0, 255, 0]    # Green
        frame[0:160, 426:640] = [0, 0, 255]    # Blue
        frame[160:320, 0:213] = [255, 255, 0]  # Yellow
        frame[160:320, 213:426] = [255, 0, 255] # Magenta
        frame[160:320, 426:640] = [0, 255, 255] # Cyan
        frame[320:480, 0:213] = [128, 128, 128] # Gray
        frame[320:480, 213:426] = [255, 255, 255] # White
        frame[320:480, 426:640] = [64, 64, 64]  # Dark gray
        
        self.panel.set_frame(frame)
        self.panel.set_loading(False)
        self.panel.set_error("")
        print("Test frame displayed (try zooming and panning!)")
    
    def clear_panel(self):
        self.panel.set_loading(False)
        self.panel.set_error("")
        self.panel.video_label.clear()
        print("Panel cleared")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    demo = CameraPanelDemo()
    demo.show()
    sys.exit(app.exec_())
