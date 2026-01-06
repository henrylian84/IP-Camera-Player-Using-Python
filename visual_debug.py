#!/usr/bin/env python3
"""
Visual debug - adds a bright border to tree view to make it visible.
"""

import sys
from PyQt5.QtWidgets import QApplication
from ip_camera_player import Windows

def main():
    app = QApplication(sys.argv)
    window = Windows()
    
    # Add a bright border to tree view to make it visible
    window.camera_tree_view.setStyleSheet("""
        QTreeWidget {
            background-color: #FF0000;  /* Bright red background */
            color: white;
            border: 5px solid #00FF00;  /* Bright green border */
            font-size: 20px;
            font-weight: bold;
        }
        QTreeWidget::item {
            height: 40px;
            padding: 10px;
            background-color: #0000FF;  /* Blue items */
        }
    """)
    
    # Also make sidebar more visible
    window.left_sidebar.setStyleSheet("""
        QWidget {
            background-color: #FFFF00;  /* Yellow sidebar */
            border-right: 10px solid #FF00FF;  /* Magenta border */
        }
    """)
    
    print("=" * 60)
    print("Visual Debug Mode")
    print("=" * 60)
    print("The tree view should now have:")
    print("  - RED background")
    print("  - GREEN border (5px)")
    print("  - BLUE items")
    print("")
    print("The sidebar should have:")
    print("  - YELLOW background")
    print("  - MAGENTA right border")
    print("")
    print("If you can't see these colors, the components aren't rendering.")
    print("=" * 60)
    
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
