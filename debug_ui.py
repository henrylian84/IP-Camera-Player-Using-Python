#!/usr/bin/env python3
"""
Debug script to check UI component visibility.
"""

import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from ip_camera_player import Windows

def debug_ui():
    """Debug UI component visibility."""
    app = QApplication(sys.argv)
    window = Windows()
    window.show()  # Show the window
    
    print("=" * 60)
    print("UI Component Debug")
    print("=" * 60)
    
    # Check sidebar
    print(f"\n📦 Left Sidebar:")
    print(f"   Exists: {window.left_sidebar is not None}")
    print(f"   Visible: {window.left_sidebar.isVisible()}")
    print(f"   Width: {window.left_sidebar.width()}")
    print(f"   Height: {window.left_sidebar.height()}")
    print(f"   Collapsed: {window.left_sidebar.is_collapsed}")
    
    # Check tree view
    print(f"\n🌲 Tree View:")
    print(f"   Exists: {window.camera_tree_view is not None}")
    print(f"   Visible: {window.camera_tree_view.isVisible()}")
    print(f"   Width: {window.camera_tree_view.width()}")
    print(f"   Height: {window.camera_tree_view.height()}")
    print(f"   Parent: {window.camera_tree_view.parent()}")
    
    # Check if tree view is in sidebar
    print(f"\n🔗 Tree View in Sidebar:")
    print(f"   Sidebar has tree_view attr: {hasattr(window.left_sidebar, 'camera_tree_view')}")
    print(f"   Sidebar.camera_tree_view is window.camera_tree_view: {window.left_sidebar.camera_tree_view is window.camera_tree_view}")
    
    # Check tree layout
    print(f"\n📐 Tree Layout:")
    print(f"   Layout exists: {window.left_sidebar.tree_layout is not None}")
    print(f"   Tree in layout: {window.left_sidebar.tree_layout.indexOf(window.camera_tree_view)}")
    print(f"   Layout count: {window.left_sidebar.tree_layout.count()}")
    
    # List all widgets in tree layout
    print(f"\n   Widgets in tree_layout:")
    for i in range(window.left_sidebar.tree_layout.count()):
        item = window.left_sidebar.tree_layout.itemAt(i)
        if item:
            widget = item.widget()
            if widget:
                print(f"      [{i}] {widget.__class__.__name__} - visible: {widget.isVisible()}")
    
    # Check cameras
    cameras = window.camera_manager.get_all_cameras()
    print(f"\n📷 Cameras:")
    print(f"   Count: {len(cameras)}")
    for cam in cameras:
        print(f"      - {cam.name} ({cam.location})")
    
    # Check tree view items
    print(f"\n🌳 Tree View Items:")
    print(f"   Top level items: {window.camera_tree_view.topLevelItemCount()}")
    for i in range(window.camera_tree_view.topLevelItemCount()):
        location_node = window.camera_tree_view.topLevelItem(i)
        print(f"      Location: {location_node.text(0)} - {location_node.childCount()} cameras")
        for j in range(location_node.childCount()):
            camera_item = location_node.child(j)
            print(f"         Camera: {camera_item.text(0)}")
    
    print("\n" + "=" * 60)
    print("Window is now showing. Check if you can see the sidebar.")
    print("Press Ctrl+C to exit.")
    print("=" * 60)
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    debug_ui()
