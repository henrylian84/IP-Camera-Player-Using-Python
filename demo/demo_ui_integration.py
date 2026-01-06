#!/usr/bin/env python3
"""
Demo script to visually verify the UI integration for task 15.
Shows the integrated TopNavigationBar, LeftSidebar with CameraTreeView, and camera grid.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import QApplication
from ip_camera_player import Windows

def main():
    """Run the demo application with integrated UI components."""
    app = QApplication(sys.argv)
    
    # Create main window with integrated UI
    window = Windows()
    
    # Show the window
    window.show()
    
    print("=" * 60)
    print("UI Integration Demo - Task 15")
    print("=" * 60)
    print("\nIntegrated Components:")
    print("  ✓ TopNavigationBar at the top")
    print("  ✓ LeftSidebar on the left with CameraTreeView")
    print("  ✓ Camera grid in the center")
    print("  ✓ Control buttons at the bottom")
    print("\nFeatures to test:")
    print("  1. Click Settings button in top navigation bar")
    print("  2. Add cameras and see them appear in tree view")
    print("  3. Click cameras in tree view to select them")
    print("  4. Double-click cameras in tree view for fullscreen")
    print("  5. Click collapse button (◀) to collapse sidebar")
    print("  6. Cameras are organized by location in tree view")
    print("\nPress Ctrl+C or close window to exit")
    print("=" * 60)
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
