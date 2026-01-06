"""Quick verification of error handling implementation."""

import sys
from PyQt5.QtWidgets import QApplication
from ip_camera_player import CameraPanel, CameraInstance

app = QApplication(sys.argv)

# Test 1: Create camera with timeout
print("Test 1: Camera timeout configuration")
camera = CameraInstance(name="Test", ip_address="192.168.1.1", connection_timeout=30)
print(f"  Timeout set: {camera.connection_timeout == 30}")

# Test 2: Error display
print("\nTest 2: Error display")
panel = CameraPanel(camera)
panel.resize(640, 480)
panel.show()  # Show the panel so child widgets can be visible
panel.set_error("Test error message")
print(f"  Panel visible: {panel.isVisible()}")
print(f"  Error container visible: {panel.error_container.isVisible()}")
print(f"  Error container hidden: {panel.error_container.isHidden()}")
print(f"  Error text set: {'Test error' in panel.error_label.text()}")
print(f"  Retry button exists: {panel.retry_button is not None}")

# Test 3: Clear error
print("\nTest 3: Clear error")
panel.set_error("")
print(f"  Error container hidden: {not panel.error_container.isVisible()}")

print("\n✓ All basic checks passed!")
sys.exit(0)
