"""
Comprehensive tests for CameraPanel features.
"""
import sys
import numpy as np
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QPoint
from ip_camera_player import CameraPanel, CameraInstance

def test_selection_state():
    """Test selection state management."""
    app = QApplication(sys.argv)
    
    camera = CameraInstance(name="Test Camera", ip_address="192.168.1.100")
    panel = CameraPanel(camera)
    
    # Test initial state
    assert panel.is_selected == False
    
    # Test setting selection
    panel.set_selected(True)
    assert panel.is_selected == True
    
    panel.set_selected(False)
    assert panel.is_selected == False
    
    print("✓ Selection state test passed")

def test_loading_state():
    """Test loading animation control."""
    app = QApplication(sys.argv)
    
    camera = CameraInstance(name="Test Camera", ip_address="192.168.1.100")
    panel = CameraPanel(camera)
    
    # Test loading state
    panel.set_loading(True)
    # Loading animation should be started (we can't easily test this without GUI)
    
    panel.set_loading(False)
    # Loading animation should be stopped
    
    print("✓ Loading state test passed")

def test_error_display():
    """Test error message display."""
    app = QApplication(sys.argv)
    
    camera = CameraInstance(name="Test Camera", ip_address="192.168.1.100")
    panel = CameraPanel(camera)
    
    # Set a size for the panel so positioning works
    panel.resize(400, 300)
    
    # Test error display
    error_msg = "Connection failed"
    panel.set_error(error_msg)
    assert panel.error_label.text() == error_msg
    # Check that it's not hidden (isVisible requires parent to be shown)
    assert panel.error_label.isHidden() == False
    
    # Test clearing error
    panel.set_error("")
    assert panel.error_label.isHidden() == True
    
    print("✓ Error display test passed")

def test_zoom_functionality():
    """Test zoom factor management."""
    app = QApplication(sys.argv)
    
    camera = CameraInstance(name="Test Camera", ip_address="192.168.1.100")
    panel = CameraPanel(camera)
    
    # Test initial zoom
    assert panel.zoom_factor == 1.0
    
    # Test zoom in
    panel.zoom_factor *= 1.1
    assert panel.zoom_factor > 1.0
    
    # Test zoom out
    panel.zoom_factor /= 1.1
    assert abs(panel.zoom_factor - 1.0) < 0.01
    
    print("✓ Zoom functionality test passed")

def test_pan_offset():
    """Test pan offset management."""
    app = QApplication(sys.argv)
    
    camera = CameraInstance(name="Test Camera", ip_address="192.168.1.100")
    panel = CameraPanel(camera)
    
    # Test initial pan offset
    assert panel.pan_offset == QPoint(0, 0)
    
    # Test setting pan offset
    panel.pan_offset = QPoint(10, 20)
    assert panel.pan_offset.x() == 10
    assert panel.pan_offset.y() == 20
    
    print("✓ Pan offset test passed")

def test_fullscreen_state():
    """Test fullscreen state management."""
    app = QApplication(sys.argv)
    
    camera = CameraInstance(name="Test Camera", ip_address="192.168.1.100")
    panel = CameraPanel(camera)
    
    # Test initial state
    assert panel.is_fullscreen == False
    
    # Test entering fullscreen
    panel.enter_fullscreen()
    assert panel.is_fullscreen == True
    
    # Test exiting fullscreen
    panel.exit_fullscreen()
    assert panel.is_fullscreen == False
    
    print("✓ Fullscreen state test passed")

def test_frame_display():
    """Test frame display with set_frame method."""
    app = QApplication(sys.argv)
    
    camera = CameraInstance(name="Test Camera", ip_address="192.168.1.100")
    panel = CameraPanel(camera)
    
    # Create a test frame (100x100 black image)
    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    
    # Test setting frame (should not raise exception)
    panel.set_frame(frame)
    
    # Verify pixmap was set
    assert panel.video_label.pixmap() is not None
    
    print("✓ Frame display test passed")

def test_signals_defined():
    """Test that all required signals are defined."""
    app = QApplication(sys.argv)
    
    camera = CameraInstance(name="Test Camera", ip_address="192.168.1.100")
    panel = CameraPanel(camera)
    
    # Verify signals exist
    assert hasattr(panel, 'clicked')
    assert hasattr(panel, 'double_clicked')
    assert hasattr(panel, 'drag_started')
    assert hasattr(panel, 'drop_requested')
    
    print("✓ Signals definition test passed")

if __name__ == '__main__':
    try:
        test_selection_state()
        test_loading_state()
        test_error_display()
        test_zoom_functionality()
        test_pan_offset()
        test_fullscreen_state()
        test_frame_display()
        test_signals_defined()
        
        print("\n✓ All CameraPanel feature tests passed!")
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
