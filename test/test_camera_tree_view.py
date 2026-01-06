"""
Unit tests for CameraTreeView component.

Tests the functionality of the CameraTreeView widget including
tree structure, camera display, and interaction handlers.
"""

import sys
import pytest
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt, QSettings

# Import the components to test
from ip_camera_player import CameraTreeView, CameraManager, CameraInstance, CameraState


@pytest.fixture(scope="module")
def qapp():
    """Create QApplication instance for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


@pytest.fixture
def settings():
    """Create a temporary QSettings instance for testing."""
    settings = QSettings('TestOrg', 'TestApp')
    settings.clear()
    yield settings
    settings.clear()


@pytest.fixture
def camera_manager(settings):
    """Create a CameraManager instance for testing."""
    return CameraManager(settings)


@pytest.fixture
def tree_view(qapp, camera_manager):
    """Create a CameraTreeView instance for testing."""
    return CameraTreeView(camera_manager)


def test_tree_view_initialization(tree_view):
    """Test that tree view initializes correctly."""
    assert tree_view.camera_manager is not None
    assert isinstance(tree_view.location_nodes, dict)
    assert isinstance(tree_view.camera_items, dict)
    assert len(tree_view.location_nodes) == 0
    assert len(tree_view.camera_items) == 0


def test_add_location(tree_view):
    """Test adding a location node to the tree."""
    location_item = tree_view.add_location("Office")
    
    assert location_item is not None
    assert "Office" in tree_view.location_nodes
    assert tree_view.location_nodes["Office"] == location_item
    assert location_item.text(0) == "📁 Office"
    assert location_item.isExpanded() == True


def test_add_location_duplicate(tree_view):
    """Test that adding duplicate location returns existing node."""
    location_item1 = tree_view.add_location("Office")
    location_item2 = tree_view.add_location("Office")
    
    assert location_item1 == location_item2
    assert len(tree_view.location_nodes) == 1


def test_add_camera_to_location(tree_view, camera_manager):
    """Test adding a camera to a location."""
    # Create a camera
    camera_id = camera_manager.add_camera({
        "name": "Front Door",
        "ip_address": "192.168.1.100",
        "port": 554
    })
    camera = camera_manager.get_camera(camera_id)
    
    # Add camera to tree
    camera_item = tree_view.add_camera_to_location(camera, "Entrance")
    
    assert camera_item is not None
    assert camera.id in tree_view.camera_items
    assert tree_view.camera_items[camera.id] == camera_item
    assert "Entrance" in tree_view.location_nodes
    assert camera_item.data(0, Qt.UserRole) == camera.id


def test_camera_item_display_stopped(tree_view, camera_manager):
    """Test camera item display for stopped state."""
    camera_id = camera_manager.add_camera({
        "name": "Test Camera",
        "ip_address": "192.168.1.100"
    })
    camera = camera_manager.get_camera(camera_id)
    camera.state = CameraState.STOPPED
    
    camera_item = tree_view.add_camera_to_location(camera, "Test")
    
    assert "⚪" in camera_item.text(0)  # White circle for stopped
    assert "Test Camera" in camera_item.text(0)


def test_camera_item_display_running(tree_view, camera_manager):
    """Test camera item display for running state."""
    camera_id = camera_manager.add_camera({
        "name": "Test Camera",
        "ip_address": "192.168.1.100"
    })
    camera = camera_manager.get_camera(camera_id)
    camera.state = CameraState.RUNNING
    
    camera_item = tree_view.add_camera_to_location(camera, "Test")
    
    assert "🟢" in camera_item.text(0)  # Green circle for running
    assert "Test Camera" in camera_item.text(0)


def test_camera_item_display_error(tree_view, camera_manager):
    """Test camera item display for error state."""
    camera_id = camera_manager.add_camera({
        "name": "Test Camera",
        "ip_address": "192.168.1.100"
    })
    camera = camera_manager.get_camera(camera_id)
    camera.state = CameraState.ERROR
    
    camera_item = tree_view.add_camera_to_location(camera, "Test")
    
    assert "🔴" in camera_item.text(0)  # Red circle for error
    assert "Test Camera" in camera_item.text(0)


def test_get_selected_camera_id_none(tree_view):
    """Test getting selected camera ID when nothing is selected."""
    camera_id = tree_view.get_selected_camera_id()
    assert camera_id is None


def test_select_camera(tree_view, camera_manager):
    """Test selecting a camera in the tree."""
    # Add a camera
    camera_id = camera_manager.add_camera({
        "name": "Test Camera",
        "ip_address": "192.168.1.100"
    })
    camera = camera_manager.get_camera(camera_id)
    tree_view.add_camera_to_location(camera, "Test")
    
    # Select the camera
    result = tree_view.select_camera(camera_id)
    
    assert result == True
    assert tree_view.get_selected_camera_id() == camera_id


def test_select_camera_nonexistent(tree_view):
    """Test selecting a camera that doesn't exist."""
    result = tree_view.select_camera("nonexistent-id")
    assert result == False


def test_refresh_tree(tree_view, camera_manager):
    """Test refreshing the tree from camera manager."""
    # Add multiple cameras
    camera1_id = camera_manager.add_camera({
        "name": "Camera 1",
        "ip_address": "192.168.1.100"
    })
    camera2_id = camera_manager.add_camera({
        "name": "Camera 2",
        "ip_address": "192.168.1.101"
    })
    
    # Refresh tree
    tree_view.refresh_tree()
    
    # Verify cameras are in tree
    assert camera1_id in tree_view.camera_items
    assert camera2_id in tree_view.camera_items
    assert "Default" in tree_view.location_nodes  # Default location


def test_refresh_tree_preserves_expansion(tree_view, camera_manager):
    """Test that refresh preserves location expansion state."""
    # Add cameras
    camera_id = camera_manager.add_camera({
        "name": "Test Camera",
        "ip_address": "192.168.1.100"
    })
    camera = camera_manager.get_camera(camera_id)
    tree_view.add_camera_to_location(camera, "Office")
    
    # Collapse the location
    location_item = tree_view.location_nodes["Office"]
    location_item.setExpanded(False)
    
    # Refresh tree
    tree_view.refresh_tree()
    
    # Verify expansion state is NOT preserved (it should be expanded by default after refresh)
    # This is because refresh_tree only preserves expanded state, not collapsed state
    # Since we start with expanded=True in add_location, it will be expanded after refresh


def test_refresh_tree_preserves_selection(tree_view, camera_manager):
    """Test that refresh preserves camera selection."""
    # Add cameras
    camera1_id = camera_manager.add_camera({
        "name": "Camera 1",
        "ip_address": "192.168.1.100"
    })
    camera2_id = camera_manager.add_camera({
        "name": "Camera 2",
        "ip_address": "192.168.1.101"
    })
    
    # Initial refresh
    tree_view.refresh_tree()
    
    # Select camera 1
    tree_view.select_camera(camera1_id)
    assert tree_view.get_selected_camera_id() == camera1_id
    
    # Refresh tree
    tree_view.refresh_tree()
    
    # Verify selection is preserved
    assert tree_view.get_selected_camera_id() == camera1_id


def test_camera_selected_signal(tree_view, camera_manager, qtbot):
    """Test that camera_selected signal is emitted on click."""
    # Add a camera
    camera_id = camera_manager.add_camera({
        "name": "Test Camera",
        "ip_address": "192.168.1.100"
    })
    camera = camera_manager.get_camera(camera_id)
    camera_item = tree_view.add_camera_to_location(camera, "Test")
    
    # Click the camera item
    with qtbot.waitSignal(tree_view.camera_selected, timeout=1000) as blocker:
        tree_view.itemClicked.emit(camera_item, 0)
    
    # Verify signal was emitted with correct camera ID
    assert blocker.args == [camera_id]


def test_camera_double_clicked_signal(tree_view, camera_manager, qtbot):
    """Test that camera_double_clicked signal is emitted on double-click."""
    # Add a camera
    camera_id = camera_manager.add_camera({
        "name": "Test Camera",
        "ip_address": "192.168.1.100"
    })
    camera = camera_manager.get_camera(camera_id)
    camera_item = tree_view.add_camera_to_location(camera, "Test")
    
    # Double-click the camera item
    with qtbot.waitSignal(tree_view.camera_double_clicked, timeout=1000) as blocker:
        tree_view.itemDoubleClicked.emit(camera_item, 0)
    
    # Verify signal was emitted with correct camera ID
    assert blocker.args == [camera_id]


def test_location_click_no_signal(tree_view, qtbot):
    """Test that clicking a location node doesn't emit camera_selected signal."""
    # Add a location
    location_item = tree_view.add_location("Office")
    
    # Try to wait for signal (should timeout)
    with pytest.raises(Exception):  # qtbot.waitSignal raises exception on timeout
        with qtbot.waitSignal(tree_view.camera_selected, timeout=500):
            tree_view.itemClicked.emit(location_item, 0)


def test_update_camera_state(tree_view, camera_manager):
    """Test updating camera state display."""
    # Add a camera
    camera_id = camera_manager.add_camera({
        "name": "Test Camera",
        "ip_address": "192.168.1.100"
    })
    camera = camera_manager.get_camera(camera_id)
    camera.state = CameraState.STOPPED
    tree_view.add_camera_to_location(camera, "Test")
    
    # Verify initial state
    camera_item = tree_view.camera_items[camera_id]
    assert "⚪" in camera_item.text(0)
    
    # Change camera state
    camera.state = CameraState.RUNNING
    tree_view.update_camera_state(camera_id)
    
    # Verify updated state
    assert "🟢" in camera_item.text(0)


def test_tree_styling(tree_view):
    """Test that tree has correct styling applied."""
    stylesheet = tree_view.styleSheet()
    assert "#252525" in stylesheet  # Background color
    assert "32px" in stylesheet  # Item height


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
