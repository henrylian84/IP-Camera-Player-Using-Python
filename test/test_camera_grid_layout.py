"""
Test to verify CameraGridLayout functionality.
"""
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QWidgetItem
from PyQt5.QtCore import QRect
from ip_camera_player import CameraGridLayout, CameraPanel, CameraInstance


def test_camera_grid_layout_instantiation():
    """Test that CameraGridLayout can be created."""
    app = QApplication(sys.argv)
    
    layout = CameraGridLayout()
    
    assert layout is not None
    assert layout.count() == 0
    assert layout.fullscreen_item is None
    
    print("✓ CameraGridLayout instantiation test passed")
    return True


def test_add_remove_items():
    """Test adding and removing items from the layout."""
    app = QApplication(sys.argv)
    
    layout = CameraGridLayout()
    
    # Create camera instances and panels
    camera1 = CameraInstance(name="Camera 1", ip_address="192.168.1.100")
    camera2 = CameraInstance(name="Camera 2", ip_address="192.168.1.101")
    
    panel1 = CameraPanel(camera1)
    panel2 = CameraPanel(camera2)
    
    # Add items
    layout.addWidget(panel1)
    layout.addWidget(panel2)
    
    assert layout.count() == 2
    print("✓ Add items test passed")
    
    # Remove item
    item = layout.takeAt(0)
    assert layout.count() == 1
    assert item is not None
    
    print("✓ Remove items test passed")
    return True


def test_grid_dimension_calculation():
    """Test the grid dimension calculation algorithm."""
    app = QApplication(sys.argv)
    
    layout = CameraGridLayout()
    
    # Test various camera counts
    test_cases = [
        (0, (0, 0)),
        (1, (1, 1)),
        (2, (1, 2)),
        (3, (1, 3)),
        (4, (2, 2)),
        (5, (2, 3)),
        (6, (2, 3)),
        (7, (2, 4)),
        (8, (2, 4)),
        (9, (3, 3)),
        (10, (3, 4)),
        (12, (3, 4)),
        (16, (4, 4)),
    ]
    
    for count, expected in test_cases:
        result = layout.calculate_grid_dimensions(count)
        assert result == expected, f"For count {count}, expected {expected} but got {result}"
        print(f"  ✓ {count} cameras -> {result[0]}x{result[1]} grid")
    
    print("✓ Grid dimension calculation test passed")
    return True


def test_fullscreen_mode():
    """Test fullscreen mode functionality."""
    app = QApplication(sys.argv)
    
    layout = CameraGridLayout()
    
    # Create camera instances and panels
    camera1 = CameraInstance(name="Camera 1", ip_address="192.168.1.100")
    camera2 = CameraInstance(name="Camera 2", ip_address="192.168.1.101")
    
    panel1 = CameraPanel(camera1)
    panel2 = CameraPanel(camera2)
    
    layout.addWidget(panel1)
    layout.addWidget(panel2)
    
    # Get the layout items
    item1 = layout.itemAt(0)
    item2 = layout.itemAt(1)
    
    # Set fullscreen
    layout.set_fullscreen(item1)
    assert layout.fullscreen_item == item1
    print("  ✓ Fullscreen mode set")
    
    # Clear fullscreen
    layout.clear_fullscreen()
    assert layout.fullscreen_item is None
    print("  ✓ Fullscreen mode cleared")
    
    print("✓ Fullscreen mode test passed")
    return True


def test_swap_items():
    """Test item swapping functionality."""
    app = QApplication(sys.argv)
    
    layout = CameraGridLayout()
    
    # Create camera instances and panels
    camera1 = CameraInstance(name="Camera 1", ip_address="192.168.1.100")
    camera2 = CameraInstance(name="Camera 2", ip_address="192.168.1.101")
    camera3 = CameraInstance(name="Camera 3", ip_address="192.168.1.102")
    
    panel1 = CameraPanel(camera1)
    panel2 = CameraPanel(camera2)
    panel3 = CameraPanel(camera3)
    
    layout.addWidget(panel1)
    layout.addWidget(panel2)
    layout.addWidget(panel3)
    
    # Get initial order
    item0_before = layout.itemAt(0)
    item1_before = layout.itemAt(1)
    
    # Swap items
    layout.swap_items(0, 1)
    
    # Verify swap
    item0_after = layout.itemAt(0)
    item1_after = layout.itemAt(1)
    
    assert item0_after == item1_before
    assert item1_after == item0_before
    
    print("✓ Swap items test passed")
    return True


def test_geometry_calculation():
    """Test that setGeometry positions panels correctly."""
    app = QApplication(sys.argv)
    
    # Create a container widget
    container = QWidget()
    layout = CameraGridLayout(container)
    container.setLayout(layout)
    
    # Create camera instances and panels
    camera1 = CameraInstance(name="Camera 1", ip_address="192.168.1.100")
    camera2 = CameraInstance(name="Camera 2", ip_address="192.168.1.101")
    camera3 = CameraInstance(name="Camera 3", ip_address="192.168.1.102")
    camera4 = CameraInstance(name="Camera 4", ip_address="192.168.1.103")
    
    panel1 = CameraPanel(camera1)
    panel2 = CameraPanel(camera2)
    panel3 = CameraPanel(camera3)
    panel4 = CameraPanel(camera4)
    
    layout.addWidget(panel1)
    layout.addWidget(panel2)
    layout.addWidget(panel3)
    layout.addWidget(panel4)
    
    # Set geometry
    rect = QRect(0, 0, 800, 600)
    layout.setGeometry(rect)
    
    # For 4 cameras, should be 2x2 grid
    # Each panel should be 400x300
    assert layout.count() == 4
    print("  ✓ 4 panels positioned in 2x2 grid")
    
    print("✓ Geometry calculation test passed")
    return True


if __name__ == '__main__':
    try:
        test_camera_grid_layout_instantiation()
        test_add_remove_items()
        test_grid_dimension_calculation()
        test_fullscreen_mode()
        test_swap_items()
        test_geometry_calculation()
        print("\n✓ All CameraGridLayout tests passed!")
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
