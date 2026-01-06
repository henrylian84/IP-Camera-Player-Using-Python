"""
Unit tests for TopNavigationBar component.

Tests the TopNavigationBar widget functionality including branding,
menu buttons, and status indicators.
"""

import sys
import os
import pytest

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import QApplication, QLabel
from PyQt5.QtTest import QTest
from PyQt5.QtCore import Qt
from ip_camera_player import TopNavigationBar


@pytest.fixture(scope="module")
def qapp():
    """Create QApplication instance for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


@pytest.fixture
def nav_bar(qapp):
    """Create TopNavigationBar instance for testing."""
    return TopNavigationBar()


def test_navigation_bar_creation(nav_bar):
    """Test that TopNavigationBar can be created."""
    assert nav_bar is not None
    assert nav_bar.height() == 50  # Fixed height requirement


def test_navigation_bar_styling(nav_bar):
    """Test that TopNavigationBar has correct styling."""
    style = nav_bar.styleSheet()
    assert "#2D2D2D" in style  # Background color
    assert "#3F3F3F" in style  # Border color


def test_set_branding(nav_bar):
    """Test setting branding with title."""
    nav_bar.set_branding(None, "Test Application")
    
    assert nav_bar.app_title is not None
    assert nav_bar.app_title.text() == "Test Application"
    
    # Check title styling
    title_style = nav_bar.app_title.styleSheet()
    assert "white" in title_style.lower()
    assert "16px" in title_style
    assert "bold" in title_style.lower()


def test_add_menu_button(nav_bar):
    """Test adding menu buttons."""
    callback_called = []
    
    def test_callback():
        callback_called.append(True)
    
    button = nav_bar.add_menu_button("Test Menu", test_callback)
    
    assert button is not None
    assert button.text() == "Test Menu"
    assert button in nav_bar.menu_buttons
    
    # Simulate button click
    button.click()
    
    assert len(callback_called) == 1


def test_add_multiple_menu_buttons(nav_bar):
    """Test adding multiple menu buttons."""
    nav_bar.add_menu_button("Settings", lambda: None)
    nav_bar.add_menu_button("View", lambda: None)
    nav_bar.add_menu_button("Help", lambda: None)
    
    assert len(nav_bar.menu_buttons) == 3


def test_add_status_indicator(nav_bar):
    """Test adding status indicators."""
    label = QLabel("Test Status")
    nav_bar.add_status_indicator("test_status", label)
    
    assert "test_status" in nav_bar.status_indicators
    assert nav_bar.status_indicators["test_status"] == label
    
    # Check styling
    style = label.styleSheet()
    assert "#CCCCCC" in style  # Secondary text color


def test_update_status(nav_bar):
    """Test updating status indicator values."""
    label = QLabel("Initial Status")
    nav_bar.add_status_indicator("status", label)
    
    nav_bar.update_status("status", "Updated Status")
    
    assert label.text() == "Updated Status"


def test_update_nonexistent_status(nav_bar):
    """Test updating a status indicator that doesn't exist."""
    # Should not raise an error
    nav_bar.update_status("nonexistent", "Value")


def test_menu_clicked_signal(nav_bar, qapp):
    """Test that menu_clicked signal is emitted."""
    signal_received = []
    
    def on_signal(menu_name):
        signal_received.append(menu_name)
    
    nav_bar.menu_clicked.connect(on_signal)
    
    button = nav_bar.add_menu_button("Test", lambda: None)
    button.click()
    
    # Process events to ensure signal is delivered
    qapp.processEvents()
    
    assert len(signal_received) == 1
    assert signal_received[0] == "Test"


def test_menu_button_styling(nav_bar):
    """Test that menu buttons have correct styling."""
    button = nav_bar.add_menu_button("Styled Button", lambda: None)
    
    style = button.styleSheet()
    assert "transparent" in style.lower()  # Background
    assert "white" in style.lower()  # Text color
    assert "#3F3F3F" in style  # Hover color
    assert "#0078D7" in style  # Pressed color


def test_layout_structure(nav_bar):
    """Test that navigation bar has correct layout structure."""
    assert nav_bar.left_container is not None
    assert nav_bar.center_container is not None
    assert nav_bar.right_container is not None
    
    assert nav_bar.left_layout is not None
    assert nav_bar.center_layout is not None
    assert nav_bar.right_layout is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
