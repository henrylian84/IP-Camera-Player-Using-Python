"""
Simple test to verify CameraPanel can be instantiated.
"""
import sys
from PyQt5.QtWidgets import QApplication
from ip_camera_player import CameraPanel, CameraInstance

def test_camera_panel_instantiation():
    """Test that CameraPanel can be created with a CameraInstance."""
    app = QApplication(sys.argv)
    
    # Create a camera instance
    camera = CameraInstance(
        name="Test Camera",
        ip_address="192.168.1.100",
        port=554,
        username="admin",
        password="password",
        stream_path="stream1"
    )
    
    # Create a camera panel
    panel = CameraPanel(camera)
    
    # Verify basic attributes
    assert panel.camera_instance == camera
    assert panel.is_selected == False
    assert panel.is_fullscreen == False
    assert panel.zoom_factor == 1.0
    assert panel.video_label is not None
    assert panel.error_label is not None
    assert panel.loading_animation is not None
    
    print("✓ CameraPanel instantiation test passed")
    print(f"  - Camera ID: {camera.id}")
    print(f"  - Camera Name: {camera.name}")
    print(f"  - Panel has video_label: {panel.video_label is not None}")
    print(f"  - Panel has error_label: {panel.error_label is not None}")
    print(f"  - Panel has loading_animation: {panel.loading_animation is not None}")
    
    return True

if __name__ == '__main__':
    try:
        test_camera_panel_instantiation()
        print("\n✓ All tests passed!")
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
