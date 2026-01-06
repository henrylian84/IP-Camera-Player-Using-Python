"""
Unit tests for LeftSidebar component.

Tests the basic functionality of the LeftSidebar widget including
collapse/expand behavior and tree view integration.
"""

import sys
import pytest
from PyQt5.QtWidgets import QApplication, QLabel
from PyQt5.QtCore import Qt

# Import the component to test
from ip_camera_player import LeftSidebar


@pytest.fixture(scope="module")
def qapp():
    """Create QApplication instance for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


@pytest.fixture
def sidebar(qapp):
    """Create a LeftSidebar instance for testing."""
    return LeftSidebar()


def test_sidebar_initialization(sidebar):
    """Test that sidebar initializes with correct default values."""
    assert sidebar.is_collapsed == False
    assert sidebar.expanded_width == 250
    assert sidebar.collapsed_width == 40
    assert sidebar.width() == 250  # Should start expanded


def test_sidebar_collapse(sidebar):
    """Test that sidebar collapses correctly."""
    # Initially expanded
    assert sidebar.is_collapsed == False
    assert sidebar.width() == 250
    
    # Collapse
    sidebar.set_collapsed(True)
    
    # Verify collapsed state
    assert sidebar.is_collapsed == True
    assert sidebar.width() == 40
    assert sidebar.collapse_button.text() == "▶"


def test_sidebar_expand(sidebar):
    """Test that sidebar expands correctly."""
    # Start collapsed
    sidebar.set_collapsed(True)
    assert sidebar.is_collapsed == True
    assert sidebar.width() == 40
    
    # Expand
    sidebar.set_collapsed(False)
    
    # Verify expanded state
    assert sidebar.is_collapsed == False
    assert sidebar.width() == 250
    assert sidebar.collapse_button.text() == "◀"


def test_sidebar_toggle(sidebar):
    """Test that toggle_collapse switches state correctly."""
    # Start expanded
    initial_state = sidebar.is_collapsed
    initial_width = sidebar.width()
    
    # Toggle
    sidebar.toggle_collapse()
    
    # Verify state changed
    assert sidebar.is_collapsed != initial_state
    assert sidebar.width() != initial_width
    
    # Toggle back
    sidebar.toggle_collapse()
    
    # Verify back to original state
    assert sidebar.is_collapsed == initial_state
    assert sidebar.width() == initial_width


def test_sidebar_signal_emission(sidebar, qtbot):
    """Test that collapsed_changed signal is emitted correctly."""
    # Use qtbot to track signal emissions
    with qtbot.waitSignal(sidebar.collapsed_changed, timeout=1000) as blocker:
        sidebar.set_collapsed(True)
    
    # Verify signal was emitted with correct value
    assert blocker.args == [True]
    
    # Test expand signal
    with qtbot.waitSignal(sidebar.collapsed_changed, timeout=1000) as blocker:
        sidebar.set_collapsed(False)
    
    assert blocker.args == [False]


def test_sidebar_tree_view_integration(sidebar):
    """Test that tree view can be set and retrieved."""
    # Initially no tree view
    assert sidebar.get_tree_view() is None
    
    # Create a mock tree view (using QLabel as placeholder)
    mock_tree = QLabel("Mock Tree View")
    
    # Set tree view
    sidebar.set_tree_view(mock_tree)
    
    # Verify tree view is set
    assert sidebar.get_tree_view() is mock_tree
    
    # Verify tree view is in layout
    assert mock_tree.parent() == sidebar.tree_container


def test_sidebar_tree_view_visibility_when_collapsed(sidebar):
    """Test that tree view is hidden when sidebar is collapsed."""
    # Create a mock tree view
    mock_tree = QLabel("Mock Tree View")
    sidebar.set_tree_view(mock_tree)
    
    # Show the sidebar to make widgets visible
    sidebar.show()
    
    # Initially expanded, tree should be visible
    assert mock_tree.isVisible() == True
    
    # Collapse sidebar
    sidebar.set_collapsed(True)
    
    # Tree view should be hidden
    assert mock_tree.isVisible() == False
    
    # Expand sidebar
    sidebar.set_collapsed(False)
    
    # Tree view should be visible again
    assert mock_tree.isVisible() == True


def test_sidebar_styling(sidebar):
    """Test that sidebar has correct styling applied."""
    # Check that stylesheet is applied
    stylesheet = sidebar.styleSheet()
    assert "#252525" in stylesheet  # Background color
    assert "#3F3F3F" in stylesheet  # Border color
    
    # Check collapse button styling
    button_stylesheet = sidebar.collapse_button.styleSheet()
    assert "#2D2D2D" in button_stylesheet  # Button background


def test_sidebar_dimensions(sidebar):
    """Test that sidebar respects dimension constraints."""
    # Test expanded width
    sidebar.set_collapsed(False)
    assert sidebar.width() == sidebar.expanded_width
    
    # Test collapsed width
    sidebar.set_collapsed(True)
    assert sidebar.width() == sidebar.collapsed_width


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
