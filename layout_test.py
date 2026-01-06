#!/usr/bin/env python3
"""
Minimal layout test to debug the sidebar issue.
"""

import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                              QHBoxLayout, QLabel)
from PyQt5.QtCore import Qt

def main():
    app = QApplication(sys.argv)
    window = QMainWindow()
    
    # Create central widget
    central = QWidget()
    window.setCentralWidget(central)
    
    # Create main vertical layout
    main_v_layout = QVBoxLayout(central)
    main_v_layout.setContentsMargins(0, 0, 0, 0)
    main_v_layout.setSpacing(0)
    
    # Create top bar
    top_bar = QLabel("TOP BAR")
    top_bar.setFixedHeight(50)
    top_bar.setStyleSheet("background-color: #2D2D2D; color: white;")
    top_bar.setAlignment(Qt.AlignCenter)
    main_v_layout.addWidget(top_bar)
    
    # Create horizontal layout for sidebar and content
    h_layout = QHBoxLayout()
    h_layout.setContentsMargins(0, 0, 0, 0)
    h_layout.setSpacing(0)
    
    # Create sidebar
    sidebar = QLabel("SIDEBAR\n\nThis should\nbe fully\nvisible")
    sidebar.setFixedWidth(250)
    sidebar.setStyleSheet("background-color: yellow; color: black; border-right: 5px solid magenta;")
    sidebar.setAlignment(Qt.AlignTop | Qt.AlignLeft)
    h_layout.addWidget(sidebar)
    
    # Create content area widget
    content_widget = QWidget()
    content_layout = QVBoxLayout(content_widget)
    content_layout.setContentsMargins(0, 0, 0, 0)
    
    # Create camera grid area
    grid_area = QLabel("CAMERA GRID AREA\n\nThis is the black area")
    grid_area.setStyleSheet("background-color: black; color: white;")
    grid_area.setAlignment(Qt.AlignCenter)
    content_layout.addWidget(grid_area)
    
    # Create controls
    controls = QLabel("CONTROLS")
    controls.setFixedHeight(50)
    controls.setStyleSheet("background-color: #3F3F3F; color: white;")
    controls.setAlignment(Qt.AlignCenter)
    content_layout.addWidget(controls)
    
    # Add content widget to horizontal layout with stretch
    h_layout.addWidget(content_widget, 1)
    
    # Add horizontal layout to main vertical layout
    main_v_layout.addLayout(h_layout)
    
    window.setWindowTitle("Layout Test")
    window.resize(1000, 700)
    window.show()
    
    print("=" * 60)
    print("Layout Test")
    print("=" * 60)
    print("You should see:")
    print("  - TOP BAR (dark gray) at the top")
    print("  - YELLOW SIDEBAR on the left (250px wide)")
    print("  - BLACK CAMERA GRID in the center")
    print("  - CONTROLS (gray) at the bottom")
    print("")
    print("If the sidebar is covered, there's a Qt layout issue.")
    print("=" * 60)
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
