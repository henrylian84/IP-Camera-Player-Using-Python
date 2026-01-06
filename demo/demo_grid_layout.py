"""
Visual demonstration of CameraGridLayout with different camera counts.
This script shows how the grid layout adapts to different numbers of cameras.
"""
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QLabel, QVBoxLayout, QPushButton, QHBoxLayout
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette, QColor
from ip_camera_player import CameraGridLayout, CameraPanel, CameraInstance


class GridLayoutDemo(QMainWindow):
    """Demo window showing CameraGridLayout with different camera counts."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CameraGridLayout Demo")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Create info label
        self.info_label = QLabel("Click buttons to see different grid layouts")
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet("font-size: 14px; padding: 10px;")
        main_layout.addWidget(self.info_label)
        
        # Create container for camera grid
        self.grid_container = QWidget()
        self.grid_layout = CameraGridLayout(self.grid_container)
        self.grid_container.setLayout(self.grid_layout)
        self.grid_container.setStyleSheet("background-color: #2b2b2b;")
        main_layout.addWidget(self.grid_container, stretch=1)
        
        # Create button panel
        button_layout = QHBoxLayout()
        
        camera_counts = [1, 2, 3, 4, 6, 9, 12, 16]
        for count in camera_counts:
            btn = QPushButton(f"{count} Camera{'s' if count > 1 else ''}")
            btn.clicked.connect(lambda checked, c=count: self.show_cameras(c))
            button_layout.addWidget(btn)
        
        # Add fullscreen toggle button
        self.fullscreen_btn = QPushButton("Toggle Fullscreen (Camera 1)")
        self.fullscreen_btn.clicked.connect(self.toggle_fullscreen)
        self.fullscreen_btn.setEnabled(False)
        button_layout.addWidget(self.fullscreen_btn)
        
        main_layout.addLayout(button_layout)
        
        # Store camera panels
        self.camera_panels = []
        self.is_fullscreen = False
        
        # Show initial layout with 4 cameras
        self.show_cameras(4)
    
    def show_cameras(self, count):
        """Display the specified number of cameras."""
        # Clear existing panels
        while self.grid_layout.count() > 0:
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self.camera_panels.clear()
        self.is_fullscreen = False
        
        # Create new camera panels
        colors = [
            "#e74c3c", "#3498db", "#2ecc71", "#f39c12",
            "#9b59b6", "#1abc9c", "#e67e22", "#34495e",
            "#16a085", "#27ae60", "#2980b9", "#8e44ad",
            "#c0392b", "#d35400", "#7f8c8d", "#2c3e50"
        ]
        
        for i in range(count):
            camera = CameraInstance(
                name=f"Camera {i+1}",
                ip_address=f"192.168.1.{100+i}"
            )
            panel = CameraPanel(camera)
            
            # Add colored label to show camera number
            label = QLabel(f"Camera {i+1}\n{camera.ip_address}")
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet(f"""
                background-color: {colors[i % len(colors)]};
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 20px;
                border-radius: 5px;
            """)
            
            # Replace video label with colored label for demo
            panel.video_label.hide()
            panel.layout().addWidget(label)
            
            self.grid_layout.addWidget(panel)
            self.camera_panels.append(panel)
        
        # Update info label
        rows, cols = self.grid_layout.calculate_grid_dimensions(count)
        self.info_label.setText(
            f"Displaying {count} camera{'s' if count > 1 else ''} "
            f"in {rows}x{cols} grid layout"
        )
        
        # Enable fullscreen button if cameras exist
        self.fullscreen_btn.setEnabled(count > 0)
    
    def toggle_fullscreen(self):
        """Toggle fullscreen mode for the first camera."""
        if not self.camera_panels:
            return
        
        if self.is_fullscreen:
            self.grid_layout.clear_fullscreen()
            self.info_label.setText(
                f"Displaying {len(self.camera_panels)} cameras in grid layout"
            )
            self.fullscreen_btn.setText("Toggle Fullscreen (Camera 1)")
            self.is_fullscreen = False
        else:
            item = self.grid_layout.itemAt(0)
            self.grid_layout.set_fullscreen(item)
            self.info_label.setText("Camera 1 in fullscreen mode")
            self.fullscreen_btn.setText("Exit Fullscreen")
            self.is_fullscreen = True


def main():
    """Run the demo application."""
    app = QApplication(sys.argv)
    
    # Set dark theme
    app.setStyle("Fusion")
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.WindowText, Qt.white)
    palette.setColor(QPalette.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ToolTipBase, Qt.white)
    palette.setColor(QPalette.ToolTipText, Qt.white)
    palette.setColor(QPalette.Text, Qt.white)
    palette.setColor(QPalette.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ButtonText, Qt.white)
    palette.setColor(QPalette.BrightText, Qt.red)
    palette.setColor(QPalette.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.HighlightedText, Qt.black)
    app.setPalette(palette)
    
    demo = GridLayoutDemo()
    demo.show()
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
