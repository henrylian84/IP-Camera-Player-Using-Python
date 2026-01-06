"""
IP Camera Player Application

This module implements a GUI-based IP camera player using PyQt5 and OpenCV. It provides
functionality to view RTSP streams from IP cameras with features like zoom, pan, and snapshot
capabilities.

Key Features:
    - Real-time video streaming from IP cameras
    - Camera settings management with persistence
    - Video controls (start, stop, pause)
    - Advanced viewing features (zoom, pan, fullscreen)
    - Snapshot capture with timestamp

Author: Yamil Garcia
Version: 1.0.0
"""

from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QPushButton,
                             QHBoxLayout, QVBoxLayout, QWidget, QFileDialog,
                             QLineEdit, QDialog, QComboBox, QStatusBar, QMessageBox,
                             QLayout, QListWidget, QListWidgetItem, QTreeWidget, QTreeWidgetItem)
from PyQt5.QtCore import (Qt, QThread, pyqtSignal, QPoint, QMutex, QMutexLocker,
                          QSettings, QObject, QRect, QSize)
from PyQt5.QtGui import (QImage, QPixmap, QCloseEvent, QIcon, QMovie,
                         QWheelEvent, QMouseEvent)

import sys
import cv2
import time
import numpy as np
from typing import Tuple, Dict, Optional
import os
from os import path
from datetime import datetime
import threading
from enum import Enum
import uuid
import json
from camera_security import encrypt_password, decrypt_password

SW_VERSION = '1.0.0'
CAMERA_OPENING_TIMEOUT_SECONDS = 20


class CameraState(Enum):
    """
    Enumeration representing the possible states of a camera instance.
    
    States:
        STOPPED: Camera is not streaming
        STARTING: Camera is initializing connection
        RUNNING: Camera is actively streaming
        PAUSED: Camera stream is paused
        ERROR: Camera encountered an error
    """
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"


class CameraInstance:
    """
    Represents a single camera with its configuration and runtime state.
    
    This class encapsulates all camera configuration parameters and manages
    the camera's streaming state and associated thread.
    
    Attributes:
        id (str): Unique identifier for the camera
        name (str): User-friendly camera name
        protocol (str): Connection protocol (e.g., "rtsp")
        username (str): Authentication username
        password (str): Authentication password
        ip_address (str): Camera IP address
        port (int): Connection port
        stream_path (str): RTSP stream path
        resolution (Tuple[int, int]): Video resolution (width, height)
        connection_timeout (int): Connection timeout in seconds
        state (CameraState): Current camera state
        error_message (str): Last error message if state is ERROR
        stream_thread (Optional[StreamThread]): Associated streaming thread
    """
    
    def __init__(self, 
                 camera_id: Optional[str] = None,
                 name: str = "",
                 protocol: str = "rtsp",
                 username: str = "",
                 password: str = "",
                 ip_address: str = "",
                 port: int = 554,
                 stream_path: str = "",
                 resolution: Tuple[int, int] = (1920, 1080),
                 connection_timeout: int = CAMERA_OPENING_TIMEOUT_SECONDS,
                 location: str = "Default"):
        """
        Initialize a CameraInstance.
        
        Args:
            camera_id: Unique identifier (generates UUID if None)
            name: User-friendly camera name
            protocol: Connection protocol
            username: Authentication username
            password: Authentication password
            ip_address: Camera IP address
            port: Connection port
            stream_path: RTSP stream path
            resolution: Video resolution tuple
            connection_timeout: Connection timeout in seconds (default: 20)
            location: Location/group for organizing cameras (default: "Default")
        """
        self.id = camera_id if camera_id else str(uuid.uuid4())
        self.name = name
        self.protocol = protocol
        self.username = username
        self.password = password
        self.ip_address = ip_address
        self.port = port
        self.stream_path = stream_path
        self.resolution = resolution
        self.connection_timeout = connection_timeout
        self.location = location if location else "Default"
        self.state = CameraState.STOPPED
        self.error_message = ""
        self.stream_thread: Optional[StreamThread] = None
    
    def to_dict(self) -> Dict:
        """
        Serialize camera configuration to dictionary.
        
        Encrypts the password before serialization for secure storage.
        
        WARNING: Even though password is encrypted, avoid logging this dictionary
        as it contains sensitive configuration data.
        
        Returns:
            Dictionary containing all camera configuration with encrypted password
        """
        return {
            "id": self.id,
            "name": self.name,
            "protocol": self.protocol,
            "username": self.username,
            "password": encrypt_password(self.password),  # Encrypt password before storage
            "ip_address": self.ip_address,
            "port": self.port,
            "stream_path": self.stream_path,
            "resolution": self.resolution,
            "connection_timeout": self.connection_timeout,
            "location": self.location,
            "state": self.state.value,
            "error_message": self.error_message
        }
    
    def get_safe_info(self) -> str:
        """
        Get safe string representation of camera for logging/display.
        
        Returns:
            String with camera info without credentials
        """
        return f"Camera(id={self.id}, name={self.name}, ip={self.ip_address}:{self.port}, state={self.state.value})"
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'CameraInstance':
        """
        Deserialize camera configuration from dictionary.
        
        Decrypts the password after deserialization. Handles both encrypted
        and plain text passwords for backward compatibility.
        
        Args:
            data: Dictionary containing camera configuration
            
        Returns:
            CameraInstance object
        """
        from camera_security import PasswordEncryption
        
        # Get password from data
        password_data = data.get("password", "")
        
        # Decrypt password when loading from storage
        # Handle both encrypted and plain text for backward compatibility
        if password_data:
            # Check if password appears to be encrypted
            if PasswordEncryption.is_encrypted(password_data):
                # Decrypt encrypted password
                decrypted_password = decrypt_password(password_data)
            else:
                # Use plain text password as-is (for backward compatibility)
                decrypted_password = password_data
        else:
            decrypted_password = ""
        
        camera = cls(
            camera_id=data.get("id"),
            name=data.get("name", ""),
            protocol=data.get("protocol", "rtsp"),
            username=data.get("username", ""),
            password=decrypted_password,  # Use decrypted password
            ip_address=data.get("ip_address", ""),
            port=data.get("port", 554),
            stream_path=data.get("stream_path", ""),
            resolution=tuple(data.get("resolution", (1920, 1080))),
            connection_timeout=data.get("connection_timeout", CAMERA_OPENING_TIMEOUT_SECONDS),
            location=data.get("location", "Default")
        )
        
        # Restore state if present
        state_value = data.get("state", "stopped")
        camera.state = CameraState(state_value)
        camera.error_message = data.get("error_message", "")
        
        return camera
    
    def get_url(self) -> str:
        """
        Construct RTSP URL from camera configuration.
        
        WARNING: This URL contains credentials. Never log or display this URL.
        
        Returns:
            Complete RTSP URL string with embedded credentials
        """
        if self.username and self.password:
            return f"{self.protocol}://{self.username}:{self.password}@{self.ip_address}:{self.port}/{self.stream_path}"
        else:
            return f"{self.protocol}://{self.ip_address}:{self.port}/{self.stream_path}"
    
    def get_safe_url(self) -> str:
        """
        Construct RTSP URL without credentials for safe logging/display.
        
        Returns:
            RTSP URL string without credentials
        """
        return f"{self.protocol}://{self.ip_address}:{self.port}/{self.stream_path}"
    
    def start_stream(self) -> None:
        """
        Initiate streaming for this camera.
        
        Creates and starts a StreamThread if not already running.
        Ensures proper cleanup of any existing thread before starting a new one.
        """
        # Stop any existing stream first
        if self.stream_thread is not None:
            if self.stream_thread.isRunning():
                self.stream_thread.stop_streaming()
            self.stream_thread = None
        
        # Create and start new stream thread with configured timeout
        self.state = CameraState.STARTING
        self.error_message = ""
        self.stream_thread = StreamThread(self.get_url(), self.resolution, self.id, self.connection_timeout)
        
        # Connect signals to update state
        self.stream_thread.first_frame_received.connect(self._on_first_frame_received)
        self.stream_thread.error_signal.connect(self._on_error)
        
        self.stream_thread.start_streaming(self.get_url(), self.resolution)
    
    def stop_stream(self) -> None:
        """
        Stop streaming for this camera.
        
        Stops and cleans up the associated StreamThread.
        Ensures proper thread termination and resource cleanup.
        """
        if self.stream_thread is not None:
            if self.stream_thread.isRunning():
                self.stream_thread.stop_streaming()
            
            # Disconnect signals to prevent memory leaks
            try:
                self.stream_thread.first_frame_received.disconnect()
                self.stream_thread.error_signal.disconnect()
            except TypeError:
                # Signals may not be connected, ignore
                pass
            
            self.stream_thread = None
        
        self.state = CameraState.STOPPED
        self.error_message = ""
    
    def pause_stream(self, paused: bool) -> None:
        """
        Pause or unpause streaming for this camera.
        
        Args:
            paused: True to pause, False to unpause
        """
        if self.stream_thread and self.stream_thread.isRunning():
            self.stream_thread.pause_streaming(paused)
            self.state = CameraState.PAUSED if paused else CameraState.RUNNING
    
    def take_snapshot(self) -> Optional[np.ndarray]:
        """
        Capture current frame from the camera stream.
        
        Returns:
            Current frame as numpy array, or None if not available
        """
        if self.stream_thread and self.stream_thread.isRunning():
            # Get the current frame from the stream thread
            # This is a placeholder - actual implementation will depend on
            # how frames are stored/accessed in the StreamThread
            return None
        return None
    
    def _on_first_frame_received(self, camera_id: str) -> None:
        """
        Internal callback when first frame is received.
        Updates camera state to RUNNING.
        
        Args:
            camera_id: ID of the camera (should match self.id)
        """
        if camera_id == self.id:
            self.state = CameraState.RUNNING
            self.error_message = ""
    
    def _on_error(self, camera_id: str, error_message: str) -> None:
        """
        Internal callback when an error occurs.
        Updates camera state to ERROR.
        
        Args:
            camera_id: ID of the camera (should match self.id)
            error_message: Error message from the stream thread
        """
        if camera_id == self.id:
            self.state = CameraState.ERROR
            self.error_message = error_message


class CameraManager(QObject):
    """
    Manages the collection of camera instances and handles persistence.
    
    This class provides centralized management of all cameras, including
    adding, removing, reordering, and persisting camera configurations.
    
    Signals:
        camera_added: Emitted when a camera is added (camera_id)
        camera_removed: Emitted when a camera is removed (camera_id)
        camera_updated: Emitted when a camera is updated (camera_id)
        cameras_reordered: Emitted when cameras are reordered
        selection_changed: Emitted when selected camera changes (camera_id)
    """
    
    # Define signals
    camera_added = pyqtSignal(str)
    camera_removed = pyqtSignal(str)
    camera_updated = pyqtSignal(str)
    cameras_reordered = pyqtSignal()
    selection_changed = pyqtSignal(str)
    
    def __init__(self, settings: QSettings):
        """
        Initialize the CameraManager.
        
        Args:
            settings: QSettings instance for persistence
        """
        super().__init__()
        self.cameras: list[CameraInstance] = []
        self.settings = settings
        self.selected_camera_id: Optional[str] = None
    
    def add_camera(self, config: Dict) -> Optional[str]:
        """
        Add a new camera instance.
        
        Args:
            config: Dictionary containing camera configuration
            
        Returns:
            Camera ID if successful, None if validation fails
        """
        # Validate required fields
        required_fields = ["name", "ip_address"]
        for field in required_fields:
            if not config.get(field):
                return None
        
        # Create camera instance
        camera = CameraInstance(
            name=config.get("name", ""),
            protocol=config.get("protocol", "rtsp"),
            username=config.get("username", ""),
            password=config.get("password", ""),
            ip_address=config.get("ip_address", ""),
            port=config.get("port", 554),
            stream_path=config.get("stream_path", ""),
            resolution=config.get("resolution", (1920, 1080)),
            location=config.get("location", "Default")
        )
        
        self.cameras.append(camera)
        
        # Attempt to save settings
        if not self.save_to_settings():
            print("Warning: Failed to persist camera addition to storage")
        
        self.camera_added.emit(camera.id)
        
        return camera.id
    
    def remove_camera(self, camera_id: str) -> bool:
        """
        Remove a camera instance.
        
        Args:
            camera_id: ID of camera to remove
            
        Returns:
            True if successful, False if camera not found
        """
        camera = self.get_camera(camera_id)
        if not camera:
            return False
        
        # Stop stream if running
        if camera.stream_thread and camera.stream_thread.isRunning():
            camera.stop_stream()
        
        # Remove from list
        self.cameras = [c for c in self.cameras if c.id != camera_id]
        
        # Clear selection if this was the selected camera
        if self.selected_camera_id == camera_id:
            self.selected_camera_id = None
        
        # Attempt to save settings
        if not self.save_to_settings():
            print("Warning: Failed to persist camera removal to storage")
        
        self.camera_removed.emit(camera_id)
        
        return True
    
    def get_camera(self, camera_id: str) -> Optional[CameraInstance]:
        """
        Retrieve a camera by ID.
        
        Args:
            camera_id: ID of camera to retrieve
            
        Returns:
            CameraInstance if found, None otherwise
        """
        for camera in self.cameras:
            if camera.id == camera_id:
                return camera
        return None
    
    def get_all_cameras(self) -> list[CameraInstance]:
        """
        Return list of all cameras.
        
        Returns:
            List of all CameraInstance objects
        """
        return self.cameras.copy()
    
    def reorder_cameras(self, camera_id: str, new_index: int) -> bool:
        """
        Change camera order in the list.
        
        Args:
            camera_id: ID of camera to reorder
            new_index: New position in the list
            
        Returns:
            True if successful, False otherwise
        """
        camera = self.get_camera(camera_id)
        if not camera:
            return False
        
        # Remove camera from current position
        self.cameras = [c for c in self.cameras if c.id != camera_id]
        
        # Insert at new position
        new_index = max(0, min(new_index, len(self.cameras)))
        self.cameras.insert(new_index, camera)
        
        # Attempt to save settings
        if not self.save_to_settings():
            print("Warning: Failed to persist camera reordering to storage")
        
        self.cameras_reordered.emit()
        
        return True
    
    def select_camera(self, camera_id: str) -> bool:
        """
        Set the selected camera.
        
        Args:
            camera_id: ID of camera to select
            
        Returns:
            True if successful, False if camera not found
        """
        camera = self.get_camera(camera_id)
        if not camera:
            return False
        
        self.selected_camera_id = camera_id
        self.selection_changed.emit(camera_id)
        
        return True
    
    def get_selected_camera(self) -> Optional[CameraInstance]:
        """
        Return the currently selected camera.
        
        Returns:
            Selected CameraInstance or None if no selection
        """
        if self.selected_camera_id:
            return self.get_camera(self.selected_camera_id)
        return None
    
    def save_to_settings(self) -> bool:
        """
        Persist all cameras to QSettings with error handling.
        
        Returns:
            True if successful, False if error occurred
        """
        try:
            cameras_data = [camera.to_dict() for camera in self.cameras]
            self.settings.setValue('cameras', json.dumps(cameras_data))
            if self.selected_camera_id:
                self.settings.setValue('selected_camera_id', self.selected_camera_id)
            
            # Sync to ensure data is written to disk
            self.settings.sync()
            
            # Check if sync was successful
            status = self.settings.status()
            if status != 0:  # QSettings.NoError = 0
                print(f"Warning: QSettings sync reported status code {status}")
                return False
            
            return True
        except Exception as e:
            print(f"Error saving camera settings: {e}")
            return False
    
    def load_from_settings(self) -> bool:
        """
        Load cameras from QSettings with comprehensive error handling.
        
        Returns:
            True if successful, False if error occurred (fallback to empty config)
        """
        try:
            # Check QSettings status before reading
            status = self.settings.status()
            if status != 0:  # QSettings.NoError = 0
                print(f"Warning: QSettings has error status {status}, using empty configuration")
                self.cameras = []
                self.selected_camera_id = None
                return False
            
            cameras_json = self.settings.value('cameras', '[]', type=str)
            
            # Handle None or empty values
            if cameras_json is None or cameras_json == '':
                cameras_json = '[]'
            
            try:
                cameras_data = json.loads(cameras_json)
                
                # Validate that cameras_data is a list
                if not isinstance(cameras_data, list):
                    print("Warning: Cameras data is not a list, using empty configuration")
                    self.cameras = []
                    self.selected_camera_id = None
                    return False
                
                # Load each camera with error handling
                loaded_cameras = []
                for data in cameras_data:
                    try:
                        camera = CameraInstance.from_dict(data)
                        loaded_cameras.append(camera)
                    except Exception as e:
                        print(f"Warning: Failed to load camera from data: {e}")
                        # Continue loading other cameras
                        continue
                
                self.cameras = loaded_cameras
                
            except json.JSONDecodeError as e:
                print(f"Error: Failed to parse camera settings JSON: {e}")
                print("Using empty camera configuration")
                self.cameras = []
                self.selected_camera_id = None
                return False
            
            # Load selected camera ID
            try:
                self.selected_camera_id = self.settings.value('selected_camera_id', None, type=str)
            except Exception as e:
                print(f"Warning: Failed to load selected camera ID: {e}")
                self.selected_camera_id = None
            
            return True
            
        except Exception as e:
            print(f"Error loading camera settings: {e}")
            print("Falling back to empty camera configuration")
            self.cameras = []
            self.selected_camera_id = None
            return False


def migrate_settings(settings: QSettings) -> None:
    """
    Migrate old single-camera settings format to new multi-camera format.
    
    This function detects if the old settings format exists and converts it
    to the new multi-camera format, preserving the existing camera configuration
    as the first camera in the list. Passwords are encrypted during migration.
    
    Args:
        settings: QSettings instance to migrate
    """
    # Check if old format exists and new format doesn't
    if settings.contains('ip') and not settings.contains('cameras'):
        # Extract old settings
        protocol = settings.value('protocol', 'rtsp', type=str)
        user = settings.value('user', '', type=str)
        password = settings.value('password', '', type=str)
        ip = settings.value('ip', '', type=str)
        port = settings.value('port', 554, type=int)
        stream_path = settings.value('stream_path', '', type=str)
        
        # Handle video resolution
        video_resolution_str = settings.value('video_resolution', '', type=str)
        if video_resolution_str:
            try:
                resolution = eval(video_resolution_str)
            except:
                resolution = (1920, 1080)
        else:
            resolution = (1920, 1080)
        
        # Create migrated camera configuration with encrypted password
        migrated_camera = {
            'id': str(uuid.uuid4()),
            'name': 'Camera 1',
            'protocol': protocol,
            'username': user,
            'password': encrypt_password(password),  # Encrypt password during migration
            'ip_address': ip,
            'port': port,
            'stream_path': stream_path,
            'resolution': resolution,
            'location': 'Default',
            'state': 'stopped',
            'error_message': ''
        }
        
        # Save in new format
        settings.setValue('cameras', json.dumps([migrated_camera]))
        settings.setValue('selected_camera_id', migrated_camera['id'])
        
        # Optionally remove old keys to clean up
        old_keys = ['protocol', 'user', 'password', 'ip', 'port', 'stream_path', 'video_resolution']
        for key in old_keys:
            if settings.contains(key):
                settings.remove(key)


class CameraPanel(QWidget):
    """
    Custom QWidget displaying a single camera stream with selection and interaction support.
    
    This widget encapsulates the display of a single camera stream, including video display,
    loading animation, error messages, selection visual feedback, zoom/pan functionality,
    fullscreen toggle, and drag-and-drop support.
    
    Signals:
        clicked: Emitted when panel is clicked (camera_id)
        double_clicked: Emitted when panel is double-clicked (camera_id)
        drag_started: Emitted when drag operation starts (camera_id)
        drop_requested: Emitted when drop occurs (source_id, target_id)
    """
    
    # Define signals
    clicked = pyqtSignal(str)
    double_clicked = pyqtSignal(str)
    drag_started = pyqtSignal(str)
    drop_requested = pyqtSignal(str, str)
    
    # Define retry signal
    retry_requested = pyqtSignal(str)
    
    def __init__(self, camera_instance: CameraInstance, parent=None):
        """
        Initialize the CameraPanel.
        
        Args:
            camera_instance: Associated CameraInstance object
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.camera_instance = camera_instance
        self.is_selected = False
        self.is_fullscreen = False
        self.zoom_factor = 1.0
        self.pan_offset = QPoint(0, 0)
        self.accepting_frames = False  # Flag to control frame updates
        
        # Panning state
        self.panning = False
        self.last_mouse_position = QPoint(0, 0)
        
        # Scaled dimensions for zoom/pan calculations
        self.scaled_width = 0
        self.scaled_height = 0
        
        # Create video display label
        self.video_label = QLabel(self)
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet("background-color: black;")
        self.video_label.setContentsMargins(0, 0, 0, 0)
        
        # Load and display offline image by default
        offline_image_path = os.path.dirname(os.path.realpath(__file__)) + "/images/camera-offline.png"
        if os.path.exists(offline_image_path):
            self.offline_pixmap = QPixmap(offline_image_path)
            # Display offline image initially
            self.show_offline_image()
        else:
            self.offline_pixmap = None
        
        # Create error display container widget
        self.error_container = QWidget(self)
        self.error_container.hide()
        
        # Create error icon label
        self.error_icon_label = QLabel(self.error_container)
        self.error_icon_label.setAlignment(Qt.AlignCenter)
        self.error_icon_label.setText("⚠")  # Warning symbol
        self.error_icon_label.setStyleSheet("""
            QLabel {
                color: #FFD700;
                background-color: transparent;
                font-size: 32px;
                font-weight: bold;
                padding: 5px;
            }
        """)
        
        # Create error display label
        self.error_label = QLabel(self.error_container)
        self.error_label.setAlignment(Qt.AlignCenter)
        self.error_label.setStyleSheet("""
            QLabel {
                color: white;
                background-color: transparent;
                padding: 10px;
                font-size: 12px;
                font-weight: 500;
            }
        """)
        self.error_label.setWordWrap(True)
        
        # Create retry button with improved styling
        self.retry_button = QPushButton("Retry Connection", self.error_container)
        self.retry_button.setStyleSheet("""
            QPushButton {
                background-color: #0078D7;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 12px;
                font-weight: 600;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #1E88E5;
            }
            QPushButton:pressed {
                background-color: #0056A3;
            }
        """)
        self.retry_button.clicked.connect(self._on_retry_clicked)
        
        # Setup error container layout with icon
        error_layout = QVBoxLayout(self.error_container)
        error_layout.addWidget(self.error_icon_label)
        error_layout.addWidget(self.error_label)
        error_layout.addWidget(self.retry_button)
        error_layout.setAlignment(Qt.AlignCenter)
        error_layout.setSpacing(10)
        error_layout.setContentsMargins(15, 15, 15, 15)
        
        # Style error container with improved appearance
        self.error_container.setStyleSheet("""
            QWidget {
                background-color: rgba(220, 53, 69, 200);
                border: 2px solid rgba(255, 255, 255, 100);
                border-radius: 8px;
            }
        """)
        
        # Create loading animation
        self.loading_animation = LoadingAnimation(
            self,
            "/images/Spinner-1s-104px.gif",
            (104, 104)
        )
        
        # Setup layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.video_label)
        self.setLayout(layout)
        
        # Apply minimal border styling with black background
        self.setStyleSheet("""
            CameraPanel {
                background-color: #000000;
                border: 1px solid #2D2D2D;
            }
        """)
        
        # Enable drag and drop
        self.setAcceptDrops(True)
        
        # Set minimum size
        self.setMinimumSize(160, 120)
    
    def set_frame(self, frame: np.ndarray) -> None:
        """
        Update the displayed video frame with zoom and pan applied.
        
        Args:
            frame: Video frame as numpy array (BGR format)
        """
        # Don't accept frames if streaming is stopped
        if not self.accepting_frames:
            return
        
        if frame is None:
            return
        
        # Convert frame to RGB format
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Get frame dimensions
        h, w, ch = frame_rgb.shape
        bytes_per_line = ch * w
        
        # Create QImage from frame
        q_image = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(q_image)
        
        # Scale to fill the panel while maintaining aspect ratio
        # This ensures the video fits perfectly within the panel
        scaled_pixmap = pixmap.scaledToWidth(
            self.video_label.width(),
            Qt.SmoothTransformation
        )
        
        # If scaled height is still larger than label height, scale by height instead
        if scaled_pixmap.height() > self.video_label.height():
            scaled_pixmap = pixmap.scaledToHeight(
                self.video_label.height(),
                Qt.SmoothTransformation
            )
        
        # Apply zoom factor
        self.scaled_width = int(self.zoom_factor * scaled_pixmap.width())
        self.scaled_height = int(self.zoom_factor * scaled_pixmap.height())
        
        # Scale pixmap with zoom factor
        if self.zoom_factor != 1.0:
            scaled_pixmap = scaled_pixmap.scaled(
                self.scaled_width,
                self.scaled_height,
                Qt.IgnoreAspectRatio,
                Qt.SmoothTransformation
            )
        else:
            self.scaled_width = scaled_pixmap.width()
            self.scaled_height = scaled_pixmap.height()
        
        # Enforce boundary limits for panning
        max_x_offset = max(0, self.scaled_width - self.video_label.width())
        max_y_offset = max(0, self.scaled_height - self.video_label.height())
        
        x_offset = max(0, min(self.pan_offset.x(), max_x_offset))
        y_offset = max(0, min(self.pan_offset.y(), max_y_offset))
        
        # Create visible portion based on panning
        visible_pixmap = scaled_pixmap.copy(
            x_offset,
            y_offset,
            self.video_label.width(),
            self.video_label.height()
        )
        
        # Display the frame
        self.video_label.setPixmap(visible_pixmap)
    
    def set_selected(self, selected: bool) -> None:
        """
        Update the selection visual state.
        
        Args:
            selected: True if panel should be selected, False otherwise
        """
        self.is_selected = selected
        self.update()  # Trigger repaint to show/hide selection border
    
    def set_loading(self, loading: bool) -> None:
        """
        Show or hide the loading animation.
        
        Args:
            loading: True to show loading animation, False to hide
        """
        if loading:
            self.loading_animation.start()
            self.error_label.hide()
        else:
            self.loading_animation.stop()
    
    def show_offline_image(self) -> None:
        """Display the offline camera image."""
        # Ensure error container is hidden (if it exists)
        if hasattr(self, 'error_container'):
            self.error_container.hide()
        
        # Stop loading animation (if it exists)
        if hasattr(self, 'loading_animation'):
            self.loading_animation.stop()
        
        if not self.offline_pixmap:
            self.video_label.setStyleSheet("background-color: #404040;")
            self.video_label.clear()
            return
        
        # Get the size to scale to
        target_size = self.video_label.size()
        
        # If label size is too small, use the panel size
        if target_size.width() < 50 or target_size.height() < 50:
            target_size = self.size()
        
        # If size is still invalid, just display the pixmap at original size
        if target_size.width() <= 0 or target_size.height() <= 0:
            self.video_label.setPixmap(self.offline_pixmap)
            self.video_label.setAlignment(Qt.AlignCenter)
            return
        
        # Scale the offline image to fit while maintaining aspect ratio
        scaled_pixmap = self.offline_pixmap.scaled(
            target_size,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.video_label.setPixmap(scaled_pixmap)
        self.video_label.setAlignment(Qt.AlignCenter)
    
    def set_error(self, message: str) -> None:
        """
        Display an error message in the panel with retry button.
        
        Args:
            message: Error message to display
        """
        if message:
            self.error_label.setText(message)
            self.loading_animation.stop()
            
            # Position error container in center (this will set size)
            self._position_error_container()
            
            # Show the container after positioning
            self.error_container.show()
            
            # Raise to top
            self.error_container.raise_()
        else:
            # When clearing error, hide error container and show offline image
            self.error_container.hide()
            # Always show offline image when clearing error (camera is stopped)
            self.show_offline_image()
    
    def _position_error_container(self) -> None:
        """Position the error container in the center of the panel."""
        # Ensure error container has a reasonable size
        max_width = max(200, int(self.width() * 0.8))
        max_height = max(150, int(self.height() * 0.8))
        
        self.error_container.setMaximumWidth(max_width)
        self.error_container.setMaximumHeight(max_height)
        
        # Force the container to recalculate its size based on contents
        self.error_container.adjustSize()
        
        # Ensure minimum size
        if self.error_container.width() < 200:
            self.error_container.setFixedWidth(200)
        if self.error_container.height() < 100:
            self.error_container.setFixedHeight(100)
        
        # Calculate center position
        x = max(0, (self.width() - self.error_container.width()) // 2)
        y = max(0, (self.height() - self.error_container.height()) // 2)
        
        self.error_container.move(x, y)
    
    def _on_retry_clicked(self) -> None:
        """
        Handle retry button click.
        
        Emits retry_requested signal with camera ID.
        """
        self.retry_requested.emit(self.camera_instance.id)
    
    def enter_fullscreen(self) -> None:
        """Expand panel to fullscreen mode."""
        self.is_fullscreen = True
        self.update()
    
    def exit_fullscreen(self) -> None:
        """Return panel from fullscreen mode."""
        self.is_fullscreen = False
        self.update()
    
    def paintEvent(self, event) -> None:
        """
        Custom paint event to draw selection border.
        
        Args:
            event: Paint event
        """
        super().paintEvent(event)
        
        if self.is_selected:
            from PyQt5.QtGui import QPainter, QPen, QColor
            
            painter = QPainter(self)
            
            # Define selection border: 3px solid #0078D7 (professional blue accent)
            selection_color = QColor(0, 120, 215)  # #0078D7
            border_width = 3  # 3px as per requirements
            
            pen = QPen(selection_color, border_width)
            painter.setPen(pen)
            
            # Draw border with proper offset to account for border width
            offset = border_width // 2
            painter.drawRect(offset, offset, self.width() - border_width, self.height() - border_width)
    
    def mousePressEvent(self, event: QMouseEvent) -> None:
        """
        Handle mouse press for selection and drag initiation.
        
        Args:
            event: Mouse event
        """
        if event.button() == Qt.LeftButton:
            # Check if this is a drag start (with some movement threshold)
            self.drag_start_position = event.pos()
            
            # Emit clicked signal for selection
            self.clicked.emit(self.camera_instance.id)
            
            # Start panning mode
            self.panning = True
            self.last_mouse_position = event.pos()
    
    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """
        Handle mouse movement for panning and drag operations.
        
        Args:
            event: Mouse event
        """
        if self.panning and event.buttons() & Qt.LeftButton:
            # Check if we should start a drag operation
            if hasattr(self, 'drag_start_position'):
                distance = (event.pos() - self.drag_start_position).manhattanLength()
                
                # If moved more than threshold, start drag
                if distance > 10:
                    self._start_drag()
                    self.panning = False
                    return
            
            # Otherwise, handle panning
            delta = event.pos() - self.last_mouse_position
            self.last_mouse_position = event.pos()
            
            # Update pan offset
            new_x = self.pan_offset.x() - delta.x()
            new_y = self.pan_offset.y() - delta.y()
            
            # Enforce boundaries
            max_x_offset = max(0, self.scaled_width - self.video_label.width())
            max_y_offset = max(0, self.scaled_height - self.video_label.height())
            
            new_x = max(0, min(new_x, max_x_offset))
            new_y = max(0, min(new_y, max_y_offset))
            
            self.pan_offset = QPoint(new_x, new_y)
    
    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """
        Handle mouse release to stop panning.
        
        Args:
            event: Mouse event
        """
        if event.button() == Qt.LeftButton:
            self.panning = False
            if hasattr(self, 'drag_start_position'):
                delattr(self, 'drag_start_position')
    
    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        """
        Handle double-click for fullscreen toggle.
        
        Args:
            event: Mouse event
        """
        if event.button() == Qt.LeftButton:
            self.double_clicked.emit(self.camera_instance.id)
    
    def wheelEvent(self, event: QWheelEvent) -> None:
        """
        Handle mouse wheel for zoom control.
        
        Args:
            event: Wheel event
        """
        # Adjust zoom factor based on wheel direction
        if event.angleDelta().y() > 0:
            self.zoom_factor *= 1.1  # Zoom in
        else:
            self.zoom_factor /= 1.1  # Zoom out
        
        # Ensure zoom factor stays within reasonable range
        self.zoom_factor = max(0.1, min(self.zoom_factor, 10.0))
    
    def _start_drag(self) -> None:
        """Initiate a drag operation for reordering."""
        from PyQt5.QtCore import QMimeData
        from PyQt5.QtGui import QDrag
        
        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText(self.camera_instance.id)
        drag.setMimeData(mime_data)
        
        # Create a pixmap for drag visual feedback
        pixmap = self.grab()
        drag.setPixmap(pixmap.scaled(200, 150, Qt.KeepAspectRatio))
        
        # Emit drag started signal
        self.drag_started.emit(self.camera_instance.id)
        
        # Execute drag
        drag.exec_(Qt.MoveAction)
    
    def dragEnterEvent(self, event) -> None:
        """
        Handle drag enter event.
        
        Args:
            event: Drag enter event
        """
        if event.mimeData().hasText():
            event.acceptProposedAction()
    
    def dragMoveEvent(self, event) -> None:
        """
        Handle drag move event.
        
        Args:
            event: Drag move event
        """
        if event.mimeData().hasText():
            event.acceptProposedAction()
    
    def dropEvent(self, event) -> None:
        """
        Handle drop event for reordering.
        
        Args:
            event: Drop event
        """
        if event.mimeData().hasText():
            source_id = event.mimeData().text()
            target_id = self.camera_instance.id
            
            if source_id != target_id:
                self.drop_requested.emit(source_id, target_id)
            
            event.acceptProposedAction()
    
    def resizeEvent(self, event) -> None:
        """
        Handle resize event to reposition error container and update offline image.
        
        Args:
            event: Resize event
        """
        super().resizeEvent(event)
        
        if self.error_container.isVisible():
            self._position_error_container()
        
        # Update offline image if camera is not streaming
        if self.camera_instance.state == CameraState.STOPPED and self.offline_pixmap:
            self.show_offline_image()


class CameraGridLayout(QLayout):
    """
    Custom QLayout that arranges camera panels in a fixed 3x3 grid.
    
    This layout manager displays exactly 9 camera panels (3 rows x 3 columns)
    with each camera maintaining a 16:9 aspect ratio (1920:1080). The layout
    responds to window resizing by adjusting panel sizes proportionally.
    
    Attributes:
        items: List of layout items (camera panels)
        fullscreen_item: Currently fullscreen item (if any)
    """
    
    GRID_ROWS = 3
    GRID_COLS = 3
    ASPECT_RATIO = 16.0 / 9.0  # 1920:1080 = 16:9
    
    def __init__(self, parent=None):
        """
        Initialize the CameraGridLayout.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.items = []
        self.fullscreen_item = None
        
        # Set minimal spacing and margins for professional appearance
        self.setSpacing(2)  # 2px spacing between panels
        self.setContentsMargins(0, 0, 0, 0)  # 0px margins
    
    def addItem(self, item):
        """
        Add a camera panel to the layout.
        
        Args:
            item: QLayoutItem to add
        """
        self.items.append(item)
        self.invalidate()
    
    def removeItem(self, item):
        """
        Remove a camera panel from the layout.
        
        Args:
            item: QLayoutItem to remove
        """
        if item in self.items:
            self.items.remove(item)
            self.invalidate()
    
    def count(self):
        """
        Return the number of items in the layout.
        
        Returns:
            Number of items
        """
        return len(self.items)
    
    def itemAt(self, index):
        """
        Return the item at the specified index.
        
        Args:
            index: Index of item to retrieve
            
        Returns:
            QLayoutItem at index, or None if out of bounds
        """
        if 0 <= index < len(self.items):
            return self.items[index]
        return None
    
    def takeAt(self, index):
        """
        Remove and return the item at the specified index.
        
        Args:
            index: Index of item to remove
            
        Returns:
            QLayoutItem at index, or None if out of bounds
        """
        if 0 <= index < len(self.items):
            item = self.items.pop(index)
            self.invalidate()
            return item
        return None
    
    def setGeometry(self, rect):
        """
        Position all camera panels in a fixed 3x3 grid within the given rectangle.
        
        Each panel maintains a 16:9 aspect ratio. The grid is centered within
        the available space. Handles both normal grid layout and fullscreen mode.
        
        Args:
            rect: QRect defining the layout area
        """
        super().setGeometry(rect)
        
        if not self.items:
            return
        
        # Handle fullscreen mode
        if self.fullscreen_item is not None:
            # Show only the fullscreen item
            for item in self.items:
                if item == self.fullscreen_item:
                    item.setGeometry(rect)
                    item.widget().show()
                else:
                    item.widget().hide()
            return
        
        # Calculate fixed 3x3 grid layout
        spacing = self.spacing()
        
        # Calculate total spacing
        total_horizontal_spacing = (self.GRID_COLS - 1) * spacing
        total_vertical_spacing = (self.GRID_ROWS - 1) * spacing
        
        # Calculate available space
        available_width = rect.width() - total_horizontal_spacing
        available_height = rect.height() - total_vertical_spacing
        
        # Calculate panel width and height maintaining 16:9 aspect ratio
        # Try to fit based on width first
        panel_width = available_width // self.GRID_COLS
        panel_height = int(panel_width / self.ASPECT_RATIO)
        
        # Check if height fits, if not, fit based on height
        total_height_needed = self.GRID_ROWS * panel_height + total_vertical_spacing
        if total_height_needed > available_height:
            panel_height = available_height // self.GRID_ROWS
            panel_width = int(panel_height * self.ASPECT_RATIO)
        
        # Calculate offset to center the grid if needed
        total_grid_width = self.GRID_COLS * panel_width + total_horizontal_spacing
        total_grid_height = self.GRID_ROWS * panel_height + total_vertical_spacing
        
        offset_x = (rect.width() - total_grid_width) // 2
        offset_y = (rect.height() - total_grid_height) // 2
        
        # Position each panel in the 3x3 grid
        for index, item in enumerate(self.items):
            row = index // self.GRID_COLS
            col = index % self.GRID_COLS
            
            # Stop if we have more items than grid spaces
            if row >= self.GRID_ROWS:
                item.widget().hide()
                continue
            
            x = rect.x() + offset_x + col * (panel_width + spacing)
            y = rect.y() + offset_y + row * (panel_height + spacing)
            
            panel_rect = QRect(x, y, panel_width, panel_height)
            item.setGeometry(panel_rect)
            item.widget().show()
    
    def sizeHint(self):
        """
        Return the preferred size for the layout.
        
        Returns:
            QSize representing preferred size
        """
        # Calculate based on 3x3 grid with 16:9 aspect ratio
        # Use a reasonable base size
        panel_width = 640  # Base panel width
        panel_height = int(panel_width / self.ASPECT_RATIO)  # 360 for 16:9
        
        spacing = self.spacing()
        total_width = self.GRID_COLS * panel_width + (self.GRID_COLS - 1) * spacing
        total_height = self.GRID_ROWS * panel_height + (self.GRID_ROWS - 1) * spacing
        
        return QSize(total_width, total_height)
    
    def minimumSize(self):
        """
        Return the minimum size for the layout.
        
        Returns:
            QSize representing minimum size
        """
        # Minimum panel size: 320x180 (maintaining 16:9 ratio)
        panel_width = 320
        panel_height = 180
        
        spacing = self.spacing()
        total_width = self.GRID_COLS * panel_width + (self.GRID_COLS - 1) * spacing
        total_height = self.GRID_ROWS * panel_height + (self.GRID_ROWS - 1) * spacing
        
        return QSize(total_width, total_height)
    
    def set_fullscreen(self, item):
        """
        Set one panel to fullscreen mode.
        
        Args:
            item: QLayoutItem to display in fullscreen
        """
        if item in self.items:
            self.fullscreen_item = item
            self.invalidate()
    
    def clear_fullscreen(self):
        """
        Return to normal grid layout from fullscreen mode.
        """
        self.fullscreen_item = None
        self.invalidate()
    
    def swap_items(self, index1, index2):
        """
        Swap the positions of two panels.
        
        Args:
            index1: Index of first panel
            index2: Index of second panel
        """
        if (0 <= index1 < len(self.items) and 
            0 <= index2 < len(self.items) and 
            index1 != index2):
            self.items[index1], self.items[index2] = self.items[index2], self.items[index1]
            self.invalidate()


# LoadingAnimation class to manage the GIF
class LoadingAnimation:
    """
    A class to manage loading animation GIF display.

    This class handles the creation and control of a loading animation overlay
    that is displayed during stream initialization.

    Attributes:
        parent: Parent widget where the animation will be displayed
        label (QLabel): Label widget that contains the animation
        movie (QMovie): QMovie instance that plays the GIF animation
    """
    def __init__(self, parent, gif_path: str, size: Tuple[int, int]):
        """
        Initialize the LoadingAnimation instance.

        Args:
            parent: Parent widget where the animation will be displayed
            gif_path: Path to the GIF file
            size: Tuple of (width, height) for the animation size
        """
        self.parent = parent

        # QLabel to display the GIF
        self.label = QLabel(parent)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setContentsMargins(0, 0, 0, 0)

        # Load the GIF using QMovie
        file_name = os.path.dirname(os.path.realpath(__file__)) + gif_path
        if path.exists(file_name):
            self.movie = QMovie(file_name)

        # Set the movie to the QLabel
        self.label.setMovie(self.movie)

        # Set the size of the gif.
        width, height = size  # unpack the Tuple
        self.label.setFixedSize(width, height)

    def start(self):
        """Start the GIF animation"""
        # Position the GIF in the center of the Parent.
        x = int(self.parent.width() / 2) - int(self.label.width() / 2)
        y = int(self.parent.height() / 2) - int(self.label.height() / 2)
        self.label.setGeometry(x, y, self.label.width(), self.label.height())
        # Start the GIF animation
        self.movie.start()
        # Show the QLabel showing the GIF
        self.label.show()

    def stop(self):
        """Stop the GIF animation"""
        self.movie.stop()  # Stop the GIF animation
        self.label.hide()  # Hide the QLabel showing the GIF


class StreamThread(QThread):
    """
    Thread class for handling video stream capture.

    This class manages the camera connection and frame capture in a separate thread
    to prevent UI blocking. It emits signals for frame updates and error conditions.

    Signals:
        frame_received: Emitted when a new frame is captured (camera_id, frame)
        first_frame_received: Emitted when the first frame is captured (camera_id)
        error_signal: Emitted when an error occurs (camera_id, error_message)
        status_signal: Emitted to update status messages (camera_id, status_message)
    """

    # Signal use to send the frame to the main thread (ui)
    frame_received = pyqtSignal(str, np.ndarray)
    # Signal used to notify that the first frame was received.
    first_frame_received = pyqtSignal(str)
    # Signal to send error messages to the UI thread.
    error_signal = pyqtSignal(str, str)
    # Signal to send status messages to the UI thread.
    status_signal = pyqtSignal(str, str)

    def __init__(self, url: str, video_res: Tuple[int, int] = (1920, 1080), camera_id: str = "", timeout: int = CAMERA_OPENING_TIMEOUT_SECONDS) -> None:
        """
        Initialize the StreamThread instance.

        Args:
            url: RTSP URL for the camera stream
            video_res: Desired video resolution as (width, height)
            camera_id: Unique identifier for the camera
            timeout: Connection timeout in seconds (default: 20)
        """
        super().__init__()

        # Class fields
        self.__url = url
        self.__cap = None
        self.__stream_is_running = False
        self.__stream_is_paused = False
        self.__video_resolution = video_res
        self.__first_frame_was_received = False
        self.__resize_frame = False
        self.__timeout = timeout
        self.__camera_id = camera_id

    def run(self) -> None:
        """
       Main thread execution method for capturing video frames.

       This method handles the camera initialization and continuous frame capture.
       It emits signals for frames and various status updates.
       """

        # Start camera initialization in a separate thread
        init_thread = threading.Thread(target=self.initialize_camera)
        init_thread.start()

        # Wait for the thread to complete or timeout
        init_thread.join(self.__timeout)

        # If the thread is still alive after the timeout, handle it as a failure
        if init_thread.is_alive():
            self.error_signal.emit(
                self.__camera_id, 
                f"Connection timeout: Failed to connect to camera within {self.__timeout} seconds. "
                "Please check camera IP address, network connection, and credentials."
            )
            self.stop_streaming()
            return

        # If camera initialization failed, stop the thread
        if not self.__cap or not self.__cap.isOpened():
            # self.error_signal.emit(f"Failed to open camera stream: {self.__url}")
            self.error_signal.emit(self.__camera_id, f"Failed to open camera stream")
            self.stop_streaming()
            return

        # Reduce buffer size for low latency
        self.__cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        # Get the stream width and height
        frame_width = self.__cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        frame_height = self.__cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        print(f'camera resolution: {frame_width, frame_height}')

        # Get the desired frame width and height
        desired_frame_width, desired_frame_height = self.__video_resolution
        print(f'requested camera resolution: {self.__video_resolution}')

        # Decide if we have to resize the frame
        if desired_frame_width != frame_width or desired_frame_height != frame_height:
            self.__resize_frame = True
            print('Resizing frames')

        while self.__stream_is_running:
            if self.__cap and self.__cap.isOpened():
                if not self.__stream_is_paused:  # to pause the streaming
                    # Read the camera frame and check for errors.
                    ret, frame = self.__cap.read()
                    if not ret:
                        self.error_signal.emit(self.__camera_id, "Error reading frame. Stopping the video stream.")
                        break

                    # Resize frame for faster processing
                    if self.__resize_frame:
                        frame = cv2.resize(frame, self.__video_resolution)

                    # Emit a signal carrying the frame.
                    self.frame_received.emit(self.__camera_id, frame)

                    # Notify when the first frame was received.
                    if not self.__first_frame_was_received:
                        self.status_signal.emit(self.__camera_id, 'Streaming started')
                        # print('Streaming started')
                        self.first_frame_received.emit(self.__camera_id)
                        self.__first_frame_was_received = True
            else:
                time.sleep(0.01)  # Sleep briefly to avoid busy-waiting
        # self.stop_streaming()

    def initialize_camera(self):
        """Camera initialization logic that runs in a separate thread"""
        self.__cap = cv2.VideoCapture(self.__url)

    def start_streaming(self, url: str, res: Tuple[int, int]) -> None:
        if not self.__stream_is_running:
            self.__url = url
            self.__video_resolution = res
            self.__stream_is_running = True
            self.__stream_is_paused = False
            self.start()  # Begins execution of the thread by calling run()
            self.status_signal.emit(self.__camera_id, 'Starting streaming')
        self.__first_frame_was_received = False

    def stop_streaming(self) -> None:
        self.status_signal.emit(self.__camera_id, 'Stopping streaming')
        self.__stream_is_running = False
        # Terminate the thread.
        self.quit()
        self.wait()
        # Release resources
        if self.__cap is not None:
            self.__cap.release()
            self.__cap = None

    def pause_streaming(self, pause: bool) -> None:
        if pause:
            self.__stream_is_paused = True
            self.status_signal.emit(self.__camera_id, 'Streaming paused')
        else:
            self.__stream_is_paused = False
            self.status_signal.emit(self.__camera_id, 'Streaming playing')

    def set_url(self, url: str) -> None:
        self.__url = url

    def get_url(self) -> str:
        return self.__url

    def set_resolution(self, res: Tuple[int, int]) -> None:
        self.__video_resolution = res

    def get_resolution(self) -> Tuple[int, int]:
        return self.__video_resolution

    def set_camera_id(self, camera_id: str) -> None:
        self.__camera_id = camera_id

    def get_camera_id(self) -> str:
        return self.__camera_id


class CameraSettings(QDialog):
    """
    Dialog for configuring camera connection settings.

    This class provides a dialog interface for users to input and modify
    camera connection parameters.

    Signals:
        camera_settings_closed: Emitted when settings are saved
        camera_settings_start: Emitted when start streaming is requested
    """

    # Signal emitted when this dialog is closed.
    camera_settings_closed = pyqtSignal(dict)
    # Signal emitted when this dialog is closed.
    camera_settings_start = pyqtSignal(dict)

    def __init__(self, parent=None):
        """
        Initialize the CameraSettings dialog.

        Args:
            parent: Parent widget for this dialog
        """

        super().__init__(parent)

        self.camera_settings_start_signal_emitted: bool = False

        self.protocol_line_edit = QLineEdit(self)
        self.protocol_line_edit.setPlaceholderText('Enter protocol')
        self.protocol_line_edit.setText(parent.protocol)

        self.user_line_edit = QLineEdit(self)
        self.user_line_edit.setPlaceholderText('Enter user name')
        self.user_line_edit.setText(parent.user)

        self.password_line_edit = QLineEdit(self)
        self.password_line_edit.setPlaceholderText('Enter password')
        self.password_line_edit.setEchoMode(QLineEdit.Password)  # Set the QLineEdit to mask input like a password
        self.password_line_edit.setText(parent.password)

        self.ip_line_edit = QLineEdit(self)
        self.ip_line_edit.setPlaceholderText('Enter camera ip address')
        self.ip_line_edit.setText(parent.ip)

        self.port_line_edit = QLineEdit(self)
        self.port_line_edit.setPlaceholderText('Enter camera port number')
        self.port_line_edit.setText(str(parent.port))

        self.stream_path_line_edit = QLineEdit(self)
        self.stream_path_line_edit.setPlaceholderText('Enter stream path')
        self.stream_path_line_edit.setText(parent.stream_path)

        self.video_res_combo_box = QComboBox(self)
        video_res = ['1080p', '720p', '480p']
        self.video_res_combo_box.addItems(video_res)
        if parent.video_resolution == (1920, 1080):
            self.video_res_combo_box.setCurrentIndex(0)
        elif parent.video_resolution == (1280, 720):
            self.video_res_combo_box.setCurrentIndex(1)
        elif parent.video_resolution == (640, 480):
            self.video_res_combo_box.setCurrentIndex(2)
        else:
            self.video_res_combo_box.setCurrentIndex(0)

        self.close_button = QPushButton("Close", self)
        self.close_button.clicked.connect(self.close)

        self.start_button = QPushButton("Start", self)
        self.start_button.setToolTip('Open and start streaming the camera')
        self.start_button.clicked.connect(self.start)

        self.init_gui()

    def init_gui(self):
        #
        layout_vertical_1 = QVBoxLayout()
        layout_vertical_1.addWidget(QLabel("Protocol"))
        layout_vertical_1.addWidget(QLabel("User Name"))
        layout_vertical_1.addWidget(QLabel("Password"))
        layout_vertical_1.addWidget(QLabel("IP Address"))
        layout_vertical_1.addWidget(QLabel("Port Number"))
        layout_vertical_1.addWidget(QLabel("Stream Path"))
        layout_vertical_1.addWidget(QLabel("Video Resolution"))

        #
        layout_vertical_2 = QVBoxLayout()
        layout_vertical_2.addWidget(self.protocol_line_edit)
        layout_vertical_2.addWidget(self.user_line_edit)
        layout_vertical_2.addWidget(self.password_line_edit)
        layout_vertical_2.addWidget(self.ip_line_edit)
        layout_vertical_2.addWidget(self.port_line_edit)
        layout_vertical_2.addWidget(self.stream_path_line_edit)
        layout_vertical_2.addWidget(self.video_res_combo_box)

        #
        layout_horizontal_1 = QHBoxLayout()
        layout_horizontal_1.addLayout(layout_vertical_1)
        layout_horizontal_1.addLayout(layout_vertical_2)

        #
        layout_horizontal_2 = QHBoxLayout()
        layout_horizontal_2.addWidget(self.start_button)
        layout_horizontal_2.addStretch(1)
        layout_horizontal_2.addWidget(self.close_button)

        #
        layout_vertical_3 = QVBoxLayout()
        layout_vertical_3.addLayout(layout_horizontal_1)
        layout_vertical_3.addLayout(layout_horizontal_2)

        # Set up setting window
        self.setLayout(layout_vertical_3)
        self.setWindowTitle('Camera Settings')
        self.setFixedSize(400, 220)

    def start(self) -> None:
        # Create a dictionary with the camera settings
        data: Dict[str, str] = {
            "Protocol": self.protocol_line_edit.text(),
            "User Name": self.user_line_edit.text(),
            "Password": self.password_line_edit.text(),
            "IP Address": self.ip_line_edit.text(),
            "Port Number": self.port_line_edit.text(),
            "Stream Path": self.stream_path_line_edit.text(),
            "Video Resolution": self.video_res_combo_box.currentText()
        }
        # Emit this signal with a dictionary
        self.camera_settings_start.emit(data)
        self.camera_settings_start_signal_emitted = True
        # Close this dialog
        self.close()

    # Overriding the closeEvent to capture when the dialog is closed
    def closeEvent(self, event: QCloseEvent) -> None:
        if not self.camera_settings_start_signal_emitted:
            # Create a dictionary with the camera settings
            data: Dict[str, str] = {
                "Protocol": self.protocol_line_edit.text(),
                "User Name": self.user_line_edit.text(),
                "Password": self.password_line_edit.text(),
                "IP Address": self.ip_line_edit.text(),
                "Port Number": self.port_line_edit.text(),
                "Stream Path": self.stream_path_line_edit.text(),
                "Video Resolution": self.video_res_combo_box.currentText()
            }
            # Emit signal with a dictionary
            self.camera_settings_closed.emit(data)
        event.accept()


class CameraConfigDialog(QDialog):
    """
    Dialog for adding or editing individual camera configuration.
    
    This dialog provides a form interface for users to input or modify
    all camera configuration parameters including connection details,
    credentials, and video settings.
    
    Attributes:
        camera_instance: Optional CameraInstance being edited (None for add mode)
        Form fields for all camera properties
    """
    
    def __init__(self, parent=None, camera_instance: Optional[CameraInstance] = None):
        """
        Initialize the CameraConfigDialog.
        
        Args:
            parent: Parent widget for this dialog
            camera_instance: Optional CameraInstance to edit (None for add mode)
        """
        super().__init__(parent)
        
        self.camera_instance = camera_instance
        self.is_edit_mode = camera_instance is not None
        
        # Create form fields with increased height for better readability
        self.name_line_edit = QLineEdit(self)
        self.name_line_edit.setPlaceholderText('Enter camera name')
        self.name_line_edit.setMinimumHeight(30)
        
        self.location_line_edit = QLineEdit(self)
        self.location_line_edit.setPlaceholderText('Enter location (e.g., Front Door, Backyard)')
        self.location_line_edit.setText('Default')
        self.location_line_edit.setMinimumHeight(30)
        
        self.protocol_combo_box = QComboBox(self)
        self.protocol_combo_box.addItems(['rtsp', 'http', 'https'])
        self.protocol_combo_box.setMinimumHeight(30)
        
        self.username_line_edit = QLineEdit(self)
        self.username_line_edit.setPlaceholderText('Enter username')
        self.username_line_edit.setMinimumHeight(30)
        
        self.password_line_edit = QLineEdit(self)
        self.password_line_edit.setPlaceholderText('Enter password')
        self.password_line_edit.setEchoMode(QLineEdit.Password)
        self.password_line_edit.setMinimumHeight(30)
        
        self.ip_address_line_edit = QLineEdit(self)
        self.ip_address_line_edit.setPlaceholderText('Enter IP address (e.g., 192.168.1.100)')
        self.ip_address_line_edit.setMinimumHeight(30)
        
        self.port_line_edit = QLineEdit(self)
        self.port_line_edit.setPlaceholderText('Enter port number')
        self.port_line_edit.setText('554')
        self.port_line_edit.setMinimumHeight(30)
        
        self.stream_path_line_edit = QLineEdit(self)
        self.stream_path_line_edit.setPlaceholderText('Enter stream path')
        self.stream_path_line_edit.setMinimumHeight(30)
        
        self.resolution_combo_box = QComboBox(self)
        self.resolution_combo_box.addItems(['1080p (1920x1080)', '720p (1280x720)', '480p (640x480)'])
        self.resolution_combo_box.setMinimumHeight(30)
        
        # Create buttons
        self.save_button = QPushButton("Save", self)
        self.save_button.clicked.connect(self.accept)
        
        self.cancel_button = QPushButton("Cancel", self)
        self.cancel_button.clicked.connect(self.reject)
        
        # Load camera data if in edit mode
        if self.is_edit_mode:
            self.load_camera(camera_instance)
        
        # Initialize GUI
        self.init_gui()
    
    def init_gui(self):
        """Initialize and set up the dialog layout."""
        # Apply dark theme to dialog
        self.setStyleSheet("""
            QDialog {
                background-color: #1E1E1E;
                color: #FFFFFF;
            }
            QLabel {
                color: #FFFFFF;
                font-size: 13px;
            }
        """)
        
        # Create labels layout
        labels_layout = QVBoxLayout()
        labels_layout.addWidget(QLabel("Camera Name:"))
        labels_layout.addWidget(QLabel("Location:"))
        labels_layout.addWidget(QLabel("Protocol:"))
        labels_layout.addWidget(QLabel("Username:"))
        labels_layout.addWidget(QLabel("Password:"))
        labels_layout.addWidget(QLabel("IP Address:"))
        labels_layout.addWidget(QLabel("Port:"))
        labels_layout.addWidget(QLabel("Stream Path:"))
        labels_layout.addWidget(QLabel("Resolution:"))
        
        # Create fields layout
        fields_layout = QVBoxLayout()
        fields_layout.addWidget(self.name_line_edit)
        fields_layout.addWidget(self.location_line_edit)
        fields_layout.addWidget(self.protocol_combo_box)
        fields_layout.addWidget(self.username_line_edit)
        fields_layout.addWidget(self.password_line_edit)
        fields_layout.addWidget(self.ip_address_line_edit)
        fields_layout.addWidget(self.port_line_edit)
        fields_layout.addWidget(self.stream_path_line_edit)
        fields_layout.addWidget(self.resolution_combo_box)
        
        # Create form layout
        form_layout = QHBoxLayout()
        form_layout.addLayout(labels_layout)
        form_layout.addLayout(fields_layout)
        
        # Create buttons layout
        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.save_button)
        buttons_layout.addStretch(1)
        buttons_layout.addWidget(self.cancel_button)
        
        # Create main layout
        main_layout = QVBoxLayout()
        main_layout.addLayout(form_layout)
        main_layout.addLayout(buttons_layout)
        
        self.setLayout(main_layout)
        
        # Set window properties
        title = "Edit Camera" if self.is_edit_mode else "Add Camera"
        self.setWindowTitle(title)
        self.setFixedSize(500, 420)
    
    def load_camera(self, camera_instance: CameraInstance):
        """
        Populate form with existing camera data.
        
        Args:
            camera_instance: CameraInstance to load into form
        """
        if not camera_instance:
            return
        
        self.name_line_edit.setText(camera_instance.name)
        self.location_line_edit.setText(camera_instance.location if camera_instance.location else "Default")
        
        # Set protocol
        protocol_index = self.protocol_combo_box.findText(camera_instance.protocol)
        if protocol_index >= 0:
            self.protocol_combo_box.setCurrentIndex(protocol_index)
        
        self.username_line_edit.setText(camera_instance.username)
        self.password_line_edit.setText(camera_instance.password)
        self.ip_address_line_edit.setText(camera_instance.ip_address)
        self.port_line_edit.setText(str(camera_instance.port))
        self.stream_path_line_edit.setText(camera_instance.stream_path)
        
        # Set resolution
        resolution = camera_instance.resolution
        if resolution == (1920, 1080):
            self.resolution_combo_box.setCurrentIndex(0)
        elif resolution == (1280, 720):
            self.resolution_combo_box.setCurrentIndex(1)
        elif resolution == (640, 480):
            self.resolution_combo_box.setCurrentIndex(2)
    
    def get_camera_data(self) -> Dict:
        """
        Extract form data as dictionary.
        
        Returns:
            Dictionary containing camera configuration
        """
        # Parse resolution
        resolution_text = self.resolution_combo_box.currentText()
        if '1920x1080' in resolution_text:
            resolution = (1920, 1080)
        elif '1280x720' in resolution_text:
            resolution = (1280, 720)
        elif '640x480' in resolution_text:
            resolution = (640, 480)
        else:
            resolution = (1920, 1080)
        
        # Parse port
        try:
            port = int(self.port_line_edit.text())
        except ValueError:
            port = 554
        
        # Get location, default to "Default" if empty
        location = self.location_line_edit.text().strip()
        if not location:
            location = "Default"
        
        return {
            "name": self.name_line_edit.text().strip(),
            "location": location,
            "protocol": self.protocol_combo_box.currentText(),
            "username": self.username_line_edit.text().strip(),
            "password": self.password_line_edit.text(),
            "ip_address": self.ip_address_line_edit.text().strip(),
            "port": port,
            "stream_path": self.stream_path_line_edit.text().strip(),
            "resolution": resolution
        }
    
    def validate(self) -> Tuple[bool, str]:
        """
        Validate form inputs with comprehensive field-specific checks.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        data = self.get_camera_data()
        
        # Validate camera name
        if not data["name"]:
            self.name_line_edit.setFocus()
            return False, "Camera name is required"
        
        if len(data["name"]) > 100:
            self.name_line_edit.setFocus()
            return False, "Camera name must be 100 characters or less"
        
        # Validate location (optional but check length if provided)
        if data["location"] and len(data["location"]) > 100:
            self.location_line_edit.setFocus()
            return False, "Location must be 100 characters or less"
        
        # Validate IP address
        if not data["ip_address"]:
            self.ip_address_line_edit.setFocus()
            return False, "IP address is required"
        
        # Basic IP address format validation
        ip_parts = data["ip_address"].split('.')
        if len(ip_parts) != 4:
            self.ip_address_line_edit.setFocus()
            return False, "IP address must be in format xxx.xxx.xxx.xxx"
        
        try:
            for part in ip_parts:
                num = int(part)
                if num < 0 or num > 255:
                    self.ip_address_line_edit.setFocus()
                    return False, "Each IP address octet must be between 0 and 255"
        except ValueError:
            self.ip_address_line_edit.setFocus()
            return False, "IP address must contain only numbers and dots"
        
        # Validate port number
        if data["port"] < 1 or data["port"] > 65535:
            self.port_line_edit.setFocus()
            return False, "Port must be between 1 and 65535"
        
        # Validate protocol
        if data["protocol"] not in ['rtsp', 'http', 'https']:
            return False, "Protocol must be rtsp, http, or https"
        
        # Validate stream path (optional but if provided, check for invalid characters)
        if data["stream_path"]:
            invalid_chars = ['<', '>', '|', '"', '?', '*']
            for char in invalid_chars:
                if char in data["stream_path"]:
                    self.stream_path_line_edit.setFocus()
                    return False, f"Stream path contains invalid character: {char}"
        
        return True, ""
    
    def accept(self):
        """Override accept to validate before closing with visual feedback."""
        # Clear any previous error styling
        self._clear_error_styling()
        
        is_valid, error_message = self.validate()
        
        if not is_valid:
            # Apply error styling to the focused field (the invalid one)
            focused_widget = self.focusWidget()
            if isinstance(focused_widget, QLineEdit):
                focused_widget.setStyleSheet("border: 2px solid red;")
            
            # Show error message
            QMessageBox.warning(self, "Validation Error", error_message)
            return
        
        super().accept()
    
    def _clear_error_styling(self):
        """Clear error styling from all input fields."""
        for widget in [self.name_line_edit, self.location_line_edit, self.ip_address_line_edit, 
                      self.port_line_edit, self.stream_path_line_edit,
                      self.username_line_edit, self.password_line_edit]:
            widget.setStyleSheet("")


class CameraListWidget(QDialog):
    """
    Dialog for managing camera configurations.
    
    This dialog provides a list view of all configured cameras with
    buttons to add, edit, and delete cameras. It integrates with
    CameraManager for all camera operations.
    
    Attributes:
        camera_manager: Reference to CameraManager instance
        camera_list_view: QListWidget showing all cameras
        Buttons for add, edit, delete, and close operations
    """
    
    def __init__(self, camera_manager: CameraManager, parent=None):
        """
        Initialize the CameraListWidget.
        
        Args:
            camera_manager: CameraManager instance
            parent: Parent widget for this dialog
        """
        super().__init__(parent)
        
        self.camera_manager = camera_manager
        
        # Create list widget
        self.camera_list_view = QListWidget(self)
        self.camera_list_view.itemSelectionChanged.connect(self.on_selection_changed)
        
        # Create buttons
        self.add_button = QPushButton("Add", self)
        self.add_button.clicked.connect(self.handle_add)
        
        self.edit_button = QPushButton("Edit", self)
        self.edit_button.clicked.connect(self.handle_edit)
        self.edit_button.setEnabled(False)
        
        self.delete_button = QPushButton("Delete", self)
        self.delete_button.clicked.connect(self.handle_delete)
        self.delete_button.setEnabled(False)
        
        self.close_button = QPushButton("Close", self)
        self.close_button.clicked.connect(self.accept)
        
        # Initialize GUI
        self.init_gui()
        
        # Connect to CameraManager signals
        self.camera_manager.camera_added.connect(lambda camera_id: self.refresh_list())
        self.camera_manager.camera_removed.connect(lambda camera_id: self.refresh_list())
        self.camera_manager.camera_updated.connect(lambda camera_id: self.refresh_list())
        
        # Initial list population
        self.refresh_list()
    
    def init_gui(self):
        """Initialize and set up the dialog layout."""
        # Apply dark theme to dialog
        self.setStyleSheet("""
            QDialog {
                background-color: #1E1E1E;
                color: #FFFFFF;
            }
        """)
        
        # Style the camera list widget with dark theme
        self.camera_list_view.setStyleSheet("""
            QListWidget {
                background-color: #2D2D2D;
                color: #FFFFFF;
                border: 1px solid #3F3F3F;
                border-radius: 4px;
                padding: 5px;
                font-size: 13px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #3F3F3F;
            }
            QListWidget::item:selected {
                background-color: rgba(0, 120, 215, 0.3);
                color: #FFFFFF;
            }
            QListWidget::item:hover {
                background-color: #3F3F3F;
            }
        """)
        
        # Style buttons consistently with dark theme
        button_style = """
            QPushButton {
                background-color: #2D2D2D;
                color: #FFFFFF;
                border: 1px solid #3F3F3F;
                padding: 10px 20px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: 600;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #3F3F3F;
                border: 1px solid #0078D7;
            }
            QPushButton:pressed {
                background-color: #0078D7;
                border: 1px solid #0078D7;
            }
            QPushButton:disabled {
                background-color: #1E1E1E;
                color: rgba(255, 255, 255, 0.5);
                border: 1px solid #2D2D2D;
            }
        """
        
        self.add_button.setStyleSheet(button_style)
        self.edit_button.setStyleSheet(button_style)
        
        # Delete button gets a different color to indicate destructive action
        self.delete_button.setStyleSheet("""
            QPushButton {
                background-color: #DC3545;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: 600;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #C82333;
            }
            QPushButton:pressed {
                background-color: #BD2130;
            }
            QPushButton:disabled {
                background-color: #1E1E1E;
                color: rgba(255, 255, 255, 0.5);
                border: 1px solid #2D2D2D;
            }
        """)
        
        # Close button gets a neutral style with dark theme
        self.close_button.setStyleSheet("""
            QPushButton {
                background-color: #2D2D2D;
                color: #FFFFFF;
                border: 1px solid #3F3F3F;
                padding: 10px 20px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: 600;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #3F3F3F;
            }
            QPushButton:pressed {
                background-color: #0078D7;
            }
        """)
        
        # Create buttons layout
        buttons_layout = QVBoxLayout()
        buttons_layout.addWidget(self.add_button)
        buttons_layout.addWidget(self.edit_button)
        buttons_layout.addWidget(self.delete_button)
        buttons_layout.addStretch(1)
        buttons_layout.addWidget(self.close_button)
        buttons_layout.setSpacing(10)
        
        # Create main layout
        main_layout = QHBoxLayout()
        main_layout.addWidget(self.camera_list_view, stretch=3)
        main_layout.addLayout(buttons_layout)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)
        
        self.setLayout(main_layout)
        
        # Set window properties
        self.setWindowTitle("Camera Settings")
        self.setMinimumSize(600, 400)
        
        # Style the dialog itself
        self.setStyleSheet("""
            QDialog {
                background-color: #F8F9FA;
            }
        """)
    
    def refresh_list(self):
        """Update the displayed camera list."""
        self.camera_list_view.clear()
        
        cameras = self.camera_manager.get_all_cameras()
        
        for camera in cameras:
            # Create display text with camera name, IP, and state
            state_icon = self._get_state_icon(camera.state)
            state_text = self._get_state_text(camera.state)
            display_text = f"{state_icon}  {camera.name}\n    {camera.ip_address}:{camera.port} - {state_text}"
            
            # Create list item
            item = QListWidgetItem(display_text)
            item.setData(Qt.UserRole, camera.id)  # Store camera ID
            
            # Set item height for better appearance
            from PyQt5.QtCore import QSize
            item.setSizeHint(QSize(0, 50))
            
            self.camera_list_view.addItem(item)
    
    def _get_state_icon(self, state: CameraState) -> str:
        """
        Get icon/symbol for camera state.
        
        Args:
            state: CameraState enum value
            
        Returns:
            String icon/symbol representing the state
        """
        if state == CameraState.STOPPED:
            return "⏹"  # Stop symbol
        elif state == CameraState.STARTING:
            return "⏳"  # Hourglass
        elif state == CameraState.RUNNING:
            return "▶"  # Play symbol
        elif state == CameraState.PAUSED:
            return "⏸"  # Pause symbol
        elif state == CameraState.ERROR:
            return "⚠"  # Warning symbol
        else:
            return "○"  # Circle
    
    def _get_state_text(self, state: CameraState) -> str:
        """
        Get text description for camera state.
        
        Args:
            state: CameraState enum value
            
        Returns:
            String description of the state
        """
        if state == CameraState.STOPPED:
            return "Stopped"
        elif state == CameraState.STARTING:
            return "Starting..."
        elif state == CameraState.RUNNING:
            return "Running"
        elif state == CameraState.PAUSED:
            return "Paused"
        elif state == CameraState.ERROR:
            return "Error"
        else:
            return "Unknown"
    
    def on_selection_changed(self):
        """Handle selection changes in the list."""
        has_selection = len(self.camera_list_view.selectedItems()) > 0
        self.edit_button.setEnabled(has_selection)
        self.delete_button.setEnabled(has_selection)
    
    def show_camera_form(self, camera_id: Optional[str] = None):
        """
        Show the camera configuration form.
        
        Args:
            camera_id: Optional camera ID for edit mode (None for add mode)
        """
        camera_instance = None
        if camera_id:
            camera_instance = self.camera_manager.get_camera(camera_id)
        
        dialog = CameraConfigDialog(self, camera_instance)
        
        if dialog.exec_() == QDialog.Accepted:
            camera_data = dialog.get_camera_data()
            
            if camera_id:
                # Edit mode - update existing camera
                if camera_instance:
                    camera_instance.name = camera_data["name"]
                    camera_instance.protocol = camera_data["protocol"]
                    camera_instance.username = camera_data["username"]
                    camera_instance.password = camera_data["password"]
                    camera_instance.ip_address = camera_data["ip_address"]
                    camera_instance.port = camera_data["port"]
                    camera_instance.stream_path = camera_data["stream_path"]
                    camera_instance.resolution = camera_data["resolution"]
                    
                    # Attempt to save and notify user if failed
                    if not self.camera_manager.save_to_settings():
                        QMessageBox.warning(
                            self,
                            "Storage Error",
                            "Failed to save camera settings to storage. "
                            "Changes may not persist after application restart."
                        )
                    
                    self.camera_manager.camera_updated.emit(camera_id)
            else:
                # Add mode - create new camera
                camera_id = self.camera_manager.add_camera(camera_data)
                
                # Check if save failed (add_camera already logs warning)
                if camera_id and self.camera_manager.settings.status() != 0:
                    QMessageBox.warning(
                        self,
                        "Storage Error",
                        "Camera was added but failed to save to storage. "
                        "Changes may not persist after application restart."
                    )
    
    def handle_add(self):
        """Handle add button click."""
        self.show_camera_form()
    
    def handle_edit(self):
        """Handle edit button click."""
        selected_items = self.camera_list_view.selectedItems()
        if not selected_items:
            return
        
        camera_id = selected_items[0].data(Qt.UserRole)
        self.show_camera_form(camera_id)
    
    def handle_delete(self):
        """Handle delete button click."""
        selected_items = self.camera_list_view.selectedItems()
        if not selected_items:
            return
        
        camera_id = selected_items[0].data(Qt.UserRole)
        camera = self.camera_manager.get_camera(camera_id)
        
        if not camera:
            return
        
        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete camera '{camera.name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.camera_manager.remove_camera(camera_id)


class TopNavigationBar(QWidget):
    """
    Custom QWidget providing the top navigation bar with branding and system controls.
    
    This widget displays application branding, menu buttons for key functions,
    and status indicators. It follows professional surveillance software styling
    with a dark theme.
    
    Attributes:
        app_logo (QLabel): Label displaying application logo/icon
        app_title (QLabel): Label displaying application name
        menu_buttons (list): List of QPushButton for menu items
        status_indicators (dict): Dictionary of status indicator widgets
    
    Signals:
        menu_clicked (str): Emitted when a menu button is clicked with menu name
    """
    
    # Define signals
    menu_clicked = pyqtSignal(str)
    
    def __init__(self, parent=None):
        """
        Initialize the TopNavigationBar.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Set fixed height to 50px as per requirements
        self.setFixedHeight(50)
        
        # Apply dark theme styling
        self.setStyleSheet("""
            QWidget {
                background-color: #2D2D2D;
                border-bottom: 1px solid #3F3F3F;
            }
        """)
        
        # Initialize attributes
        self.app_logo = None
        self.app_title = None
        self.menu_buttons = []
        self.status_indicators = {}
        
        # Create main horizontal layout
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(10, 0, 10, 0)
        self.main_layout.setSpacing(10)
        
        # Create left container for branding
        self.left_container = QWidget(self)
        self.left_layout = QHBoxLayout(self.left_container)
        self.left_layout.setContentsMargins(0, 0, 0, 0)
        self.left_layout.setSpacing(10)
        
        # Create center container for menu buttons
        self.center_container = QWidget(self)
        self.center_layout = QHBoxLayout(self.center_container)
        self.center_layout.setContentsMargins(0, 0, 0, 0)
        self.center_layout.setSpacing(5)
        
        # Create right container for status indicators
        self.right_container = QWidget(self)
        self.right_layout = QHBoxLayout(self.right_container)
        self.right_layout.setContentsMargins(0, 0, 0, 0)
        self.right_layout.setSpacing(10)
        self.right_layout.setAlignment(Qt.AlignRight)
        
        # Add containers to main layout
        self.main_layout.addWidget(self.left_container)
        self.main_layout.addStretch(1)
        self.main_layout.addWidget(self.center_container)
        self.main_layout.addStretch(1)
        self.main_layout.addWidget(self.right_container)
    
    def set_branding(self, logo_path: Optional[str], title: str) -> None:
        """
        Set application branding with logo and title.
        
        Args:
            logo_path: Path to logo image file (optional)
            title: Application title text
        """
        # Add logo if path provided
        if logo_path and os.path.exists(logo_path):
            self.app_logo = QLabel(self)
            pixmap = QPixmap(logo_path)
            # Scale logo to fit within navigation bar height
            scaled_pixmap = pixmap.scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.app_logo.setPixmap(scaled_pixmap)
            self.left_layout.addWidget(self.app_logo)
        
        # Add title
        self.app_title = QLabel(title, self)
        self.app_title.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 16px;
                font-weight: bold;
                background-color: transparent;
                border: none;
            }
        """)
        self.left_layout.addWidget(self.app_title)
    
    def add_menu_button(self, text: str, callback) -> QPushButton:
        """
        Add a menu button to the navigation bar.
        
        Args:
            text: Button text
            callback: Function to call when button is clicked
            
        Returns:
            The created QPushButton
        """
        button = QPushButton(text, self)
        button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: white;
                border: none;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #3F3F3F;
                border-radius: 4px;
            }
            QPushButton:pressed {
                background-color: #0078D7;
                border-radius: 4px;
            }
        """)
        
        # Connect to callback
        button.clicked.connect(lambda: self._on_menu_clicked(text, callback))
        
        # Add to layout and track
        self.center_layout.addWidget(button)
        self.menu_buttons.append(button)
        
        return button
    
    def add_status_indicator(self, name: str, widget: QWidget) -> None:
        """
        Add a status indicator widget to the navigation bar.
        
        Args:
            name: Identifier for the status indicator
            widget: Widget to display as status indicator
        """
        # Apply secondary text color styling
        widget.setStyleSheet("""
            QLabel {
                color: #CCCCCC;
                font-size: 12px;
                background-color: transparent;
                border: none;
            }
        """)
        
        # Add to layout and track
        self.right_layout.addWidget(widget)
        self.status_indicators[name] = widget
    
    def update_status(self, name: str, value: str) -> None:
        """
        Update a status indicator value.
        
        Args:
            name: Identifier of the status indicator
            value: New value to display
        """
        if name in self.status_indicators:
            widget = self.status_indicators[name]
            if isinstance(widget, QLabel):
                widget.setText(value)
    
    def _on_menu_clicked(self, menu_name: str, callback) -> None:
        """
        Internal handler for menu button clicks.
        
        Args:
            menu_name: Name of the menu that was clicked
            callback: Callback function to execute
        """
        # Emit signal
        self.menu_clicked.emit(menu_name)
        
        # Execute callback if provided
        if callback:
            callback()


class CameraTreeView(QTreeWidget):
    """
    Custom QTreeWidget displaying cameras organized by location.
    
    This widget provides a hierarchical tree view of cameras grouped by location,
    following professional surveillance software styling with a dark theme.
    
    Attributes:
        camera_manager: Reference to CameraManager
        location_nodes: Dictionary mapping location names to tree nodes
        camera_items: Dictionary mapping camera IDs to tree items
    
    Signals:
        camera_selected (str): Emitted when camera is clicked (camera_id)
        camera_double_clicked (str): Emitted when camera is double-clicked (camera_id)
    """
    
    # Define signals
    camera_selected = pyqtSignal(str)
    camera_double_clicked = pyqtSignal(str)
    
    def __init__(self, camera_manager: CameraManager, parent=None):
        """
        Initialize the CameraTreeView.
        
        Args:
            camera_manager: Reference to CameraManager instance
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.camera_manager = camera_manager
        self.location_nodes = {}
        self.camera_items = {}
        
        # Configure tree widget
        self.setHeaderHidden(True)
        self.setIndentation(20)
        self.setAnimated(True)
        self.setExpandsOnDoubleClick(False)  # We handle double-click for fullscreen
        
        # Apply dark theme styling
        self.setStyleSheet("""
            QTreeWidget {
                background-color: #252525;
                color: white;
                border: none;
                outline: none;
                font-size: 13px;
            }
            QTreeWidget::item {
                height: 32px;
                padding: 4px;
                border: none;
            }
            QTreeWidget::item:hover {
                background-color: #3F3F3F;
            }
            QTreeWidget::item:selected {
                background-color: rgba(0, 120, 215, 0.3);
                color: white;
            }
            QTreeWidget::item:selected:active {
                background-color: rgba(0, 120, 215, 0.5);
            }
            QTreeWidget::branch {
                background-color: #252525;
            }
            QTreeWidget::branch:has-children:!has-siblings:closed,
            QTreeWidget::branch:closed:has-children:has-siblings {
                border-image: none;
                image: url(none);
            }
            QTreeWidget::branch:open:has-children:!has-siblings,
            QTreeWidget::branch:open:has-children:has-siblings {
                border-image: none;
                image: url(none);
            }
        """)
        
        # Connect signals
        self.itemClicked.connect(self._on_item_clicked)
        self.itemDoubleClicked.connect(self._on_item_double_clicked)
    
    def add_location(self, location_name: str) -> QTreeWidgetItem:
        """
        Add a location node to the tree.
        
        Args:
            location_name: Name of the location
            
        Returns:
            QTreeWidgetItem representing the location node
        """
        # Check if location already exists
        if location_name in self.location_nodes:
            return self.location_nodes[location_name]
        
        # Create location node
        location_item = QTreeWidgetItem(self)
        location_item.setText(0, f"📁 {location_name}")
        location_item.setExpanded(True)
        
        # Style location node distinctly
        font = location_item.font(0)
        font.setBold(True)
        location_item.setFont(0, font)
        
        # Store in dictionary
        self.location_nodes[location_name] = location_item
        
        return location_item
    
    def add_camera_to_location(self, camera: CameraInstance, location: str) -> QTreeWidgetItem:
        """
        Add a camera to a location node.
        
        Args:
            camera: CameraInstance to add
            location: Location name to add camera to
            
        Returns:
            QTreeWidgetItem representing the camera
        """
        # Ensure location exists
        location_item = self.add_location(location)
        
        # Create camera item
        camera_item = QTreeWidgetItem(location_item)
        
        # Set camera name and icon based on state
        self._update_camera_item_display(camera_item, camera)
        
        # Store camera ID in item data
        camera_item.setData(0, Qt.UserRole, camera.id)
        
        # Store in dictionary
        self.camera_items[camera.id] = camera_item
        
        return camera_item
    
    def _update_camera_item_display(self, item: QTreeWidgetItem, camera: CameraInstance) -> None:
        """
        Update camera item display with name and status icon.
        
        Args:
            item: QTreeWidgetItem to update
            camera: CameraInstance with current state
        """
        # Select icon based on camera state
        # Red indicator for offline (stopped/error), Green for online (running/starting)
        if camera.state == CameraState.RUNNING:
            icon = "🟢"  # Green circle for running
        elif camera.state == CameraState.STARTING:
            icon = "🟢"  # Green circle for starting (treating as online)
        elif camera.state == CameraState.PAUSED:
            icon = "🟡"  # Yellow circle for paused
        elif camera.state == CameraState.ERROR:
            icon = "🔴"  # Red circle for error (offline)
        else:  # STOPPED
            icon = "🔴"  # Red circle for stopped (offline)
        
        # Set text with icon and camera name
        item.setText(0, f"{icon} {camera.name}")
    
    def get_selected_camera_id(self) -> Optional[str]:
        """
        Get the ID of the currently selected camera.
        
        Returns:
            Camera ID if a camera is selected, None otherwise
        """
        selected_items = self.selectedItems()
        if not selected_items:
            return None
        
        item = selected_items[0]
        camera_id = item.data(0, Qt.UserRole)
        
        # Return None if this is a location node (no camera ID)
        return camera_id if camera_id else None
    
    def select_camera(self, camera_id: str) -> bool:
        """
        Select a camera in the tree by ID.
        
        Args:
            camera_id: ID of camera to select
            
        Returns:
            True if camera was found and selected, False otherwise
        """
        if camera_id not in self.camera_items:
            return False
        
        item = self.camera_items[camera_id]
        self.setCurrentItem(item)
        
        return True
    
    def refresh_tree(self) -> None:
        """
        Rebuild tree from camera manager.
        
        Loads all cameras from the camera manager and groups them by location.
        Preserves expansion state of location nodes during refresh.
        """
        # Save expansion state
        expanded_locations = set()
        for location_name, location_item in self.location_nodes.items():
            if location_item.isExpanded():
                expanded_locations.add(location_name)
        
        # Save current selection
        selected_camera_id = self.get_selected_camera_id()
        
        # Clear existing items
        self.clear()
        self.location_nodes.clear()
        self.camera_items.clear()
        
        # Get all cameras from manager
        cameras = self.camera_manager.get_all_cameras()
        
        # Group cameras by location
        cameras_by_location = {}
        for camera in cameras:
            # Get location from camera (default to "Default" if not set)
            location = getattr(camera, 'location', 'Default')
            if not location:
                location = 'Default'
            
            if location not in cameras_by_location:
                cameras_by_location[location] = []
            cameras_by_location[location].append(camera)
        
        # Add cameras to tree grouped by location
        for location, location_cameras in sorted(cameras_by_location.items()):
            for camera in location_cameras:
                self.add_camera_to_location(camera, location)
        
        # Restore expansion state
        for location_name, location_item in self.location_nodes.items():
            if location_name in expanded_locations:
                location_item.setExpanded(True)
        
        # Restore selection
        if selected_camera_id:
            self.select_camera(selected_camera_id)
    
    def _on_item_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        """
        Handle item click event.
        
        Args:
            item: Clicked tree item
            column: Column index (always 0 for single column tree)
        """
        camera_id = item.data(0, Qt.UserRole)
        
        # Only emit signal if this is a camera item (not a location node)
        if camera_id:
            self.camera_selected.emit(camera_id)
    
    def _on_item_double_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        """
        Handle item double-click event.
        
        Args:
            item: Double-clicked tree item
            column: Column index (always 0 for single column tree)
        """
        camera_id = item.data(0, Qt.UserRole)
        
        # Only emit signal if this is a camera item (not a location node)
        if camera_id:
            self.camera_double_clicked.emit(camera_id)
    
    def update_camera_state(self, camera_id: str) -> None:
        """
        Update the display of a specific camera item based on its current state.
        
        Args:
            camera_id: ID of camera to update
        """
        if camera_id not in self.camera_items:
            return
        
        camera = self.camera_manager.get_camera(camera_id)
        if not camera:
            return
        
        item = self.camera_items[camera_id]
        self._update_camera_item_display(item, camera)


class LeftSidebar(QWidget):
    """
    Custom QWidget providing the left sidebar with camera tree navigation.
    
    This widget displays a collapsible sidebar containing a camera tree view
    for organizing and navigating cameras. It follows professional surveillance
    software styling with a dark theme.
    
    Attributes:
        camera_tree_view: CameraTreeView instance for displaying cameras
        collapse_button: QPushButton to collapse/expand sidebar
        is_collapsed: Boolean indicating collapsed state
        expanded_width: Width when expanded (default: 250)
        collapsed_width: Width when collapsed (default: 40)
    
    Signals:
        collapsed_changed (bool): Emitted when collapse state changes
    """
    
    # Define signals
    collapsed_changed = pyqtSignal(bool)
    
    def __init__(self, parent=None):
        """
        Initialize the LeftSidebar.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Initialize attributes
        self.camera_tree_view = None
        self.is_collapsed = False
        self.expanded_width = 250
        self.collapsed_width = 40
        
        # Set initial width
        self.setFixedWidth(self.expanded_width)
        
        # Apply dark theme styling with right border
        self.setStyleSheet("""
            QWidget {
                background-color: #252525;
                border-right: 1px solid #3F3F3F;
            }
        """)
        
        # Create main vertical layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Create collapse button
        self.collapse_button = QPushButton("◀", self)
        self.collapse_button.setFixedHeight(40)
        self.collapse_button.setStyleSheet("""
            QPushButton {
                background-color: #2D2D2D;
                color: white;
                border: none;
                border-bottom: 1px solid #3F3F3F;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3F3F3F;
            }
            QPushButton:pressed {
                background-color: #0078D7;
            }
        """)
        self.collapse_button.clicked.connect(self.toggle_collapse)
        
        # Add collapse button to layout
        self.main_layout.addWidget(self.collapse_button)
        
        # Create container for tree view (will be populated later)
        self.tree_container = QWidget(self)
        self.tree_layout = QVBoxLayout(self.tree_container)
        self.tree_layout.setContentsMargins(0, 0, 0, 0)
        self.tree_layout.setSpacing(0)
        
        # Add tree container to main layout
        self.main_layout.addWidget(self.tree_container)
    
    def toggle_collapse(self) -> None:
        """
        Toggle sidebar collapsed state.
        
        Switches between expanded and collapsed states with animation.
        """
        self.set_collapsed(not self.is_collapsed)
    
    def set_collapsed(self, collapsed: bool) -> None:
        """
        Set collapsed state with animation.
        
        Args:
            collapsed: True to collapse, False to expand
        """
        if self.is_collapsed == collapsed:
            return
        
        self.is_collapsed = collapsed
        
        # Update width with animation
        if collapsed:
            self.setFixedWidth(self.collapsed_width)
            self.collapse_button.setText("▶")
            # Hide tree container when collapsed
            if self.tree_container:
                self.tree_container.hide()
        else:
            self.setFixedWidth(self.expanded_width)
            self.collapse_button.setText("◀")
            # Show tree container when expanded
            if self.tree_container:
                self.tree_container.show()
        
        # Emit signal
        self.collapsed_changed.emit(self.is_collapsed)
    
    def get_tree_view(self):
        """
        Return the camera tree view.
        
        Returns:
            CameraTreeView instance or None if not set
        """
        return self.camera_tree_view
    
    def set_tree_view(self, tree_view) -> None:
        """
        Set the camera tree view for the sidebar.
        
        Args:
            tree_view: CameraTreeView instance to display
        """
        # Remove existing tree view if present
        if self.camera_tree_view:
            self.tree_layout.removeWidget(self.camera_tree_view)
            self.camera_tree_view.setParent(None)
        
        # Set new tree view
        self.camera_tree_view = tree_view
        
        if self.camera_tree_view:
            # Add to layout
            self.tree_layout.addWidget(self.camera_tree_view)
            
            # Hide if sidebar is collapsed
            if self.is_collapsed:
                self.camera_tree_view.hide()


class Windows(QMainWindow):
    """
    Main application window class.

    This class manages the main application window and coordinates all the
    functionality including video display, user interface, and camera control.

    Attributes:
        app_settings (QSettings): Application settings manager
        mutex (QMutex): Mutex for thread synchronization
        video_label (QLabel): Label for displaying video stream
        current_frame (np.ndarray): Current video frame
        zoom_factor (float): Current zoom level
        is_full_screen (bool): Fullscreen state flag
    """

    def __init__(self) -> None:
        """Initialize the main window and set up the user interface."""
        super(Windows, self).__init__()

        # Create an instance of the QSettings class to persist application data.
        self.app_settings = QSettings('IP Camera Player', 'AppSettings')
        
        # Migrate old settings to new multi-camera format if needed
        migrate_settings(self.app_settings)

        # Create a mutex to access the shared resource (frame)
        self.mutex = QMutex()

        # Create a label in the status bar to show status messages.
        self.status_bar_message_label = QLabel()

        # Create a label in the status bar to show the camera url
        self.status_bar_url = QLabel()

        # Create a label in the status bar to show the camera resolution
        self.status_bar_resolution = QLabel()

        # Create CameraManager instance for multi-camera support
        self.camera_manager = CameraManager(self.app_settings)
        
        # Create camera grid container widget (no parent initially, will be added to layout)
        self.camera_grid_container = QWidget()
        self.camera_grid_container.setStyleSheet("background-color: black;")
        
        # Create CameraGridLayout instance
        self.camera_grid_layout = CameraGridLayout(self.camera_grid_container)
        self.camera_grid_container.setLayout(self.camera_grid_layout)
        
        # Initialize camera_panels dictionary to track panel widgets
        self.camera_panels: Dict[str, CameraPanel] = {}
        
        # Keep old video_label for backward compatibility (will be hidden when using multi-camera)
        self.video_label = QLabel()
        self.video_label.setContentsMargins(0, 0, 0, 0)
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet("background-color: black;")
        self.video_label.hide()  # Hide by default, show only if no cameras configured

        # Control buttons will be created in init_gui() and added to top navigation bar

        # Read camera persisted settings if existed.
        self.protocol: str = self.app_settings.value('protocol', 'rtsp', type=str)
        self.user: str = self.app_settings.value('user', '', type=str)
        self.password: str = self.app_settings.value('password', '', type=str)
        self.ip: str = self.app_settings.value('ip', '', type=str)
        self.port: int = self.app_settings.value('port', 554, type=int)  # Default RTSP port
        self.stream_path: str = self.app_settings.value('stream_path', '', type=str)
        # Retrieve the tuple as a string
        video_resolution_str = self.app_settings.value('video_resolution', '', type=str)
        # Convert the string back to a tuple using eval
        if video_resolution_str:
            self.video_resolution: Tuple[int, int] = eval(video_resolution_str)
        else:
            self.video_resolution: Tuple[int, int] = (1920, 1080)

        # Variable for pausing
        self.is_running = False

        # Store the current frame for snapshot functionality
        self.current_frame = None

        # Store the zoom factor. Start with no zoom
        self.zoom_factor = 1.0

        # Variables for panning
        self.panning = False
        self.last_mouse_position = QPoint(0, 0)
        self.x_offset = 0
        self.y_offset = 0

        # Scaled image size (updated with zoom)
        self.scaled_width = 0
        self.scaled_height = 0

        # Variable to track full screen state
        self.is_full_screen = False

        # Initialize the GUI.
        self.init_gui()

        # Legacy single-camera support (kept for backward compatibility)
        # This is only used if no cameras are configured in the new multi-camera system
        self.url = ""
        
        # Check if we have any cameras in the new system
        cameras = self.camera_manager.get_all_cameras()
        
        if len(cameras) == 0 and self.ip:
            # No cameras in new system, but old settings exist - use legacy mode
            # Construct the url.
            self.url = f"{self.protocol}://{self.user}:{self.password}@{self.ip}:{self.port}/{self.stream_path}"
            # Update the status bar
            hidden_password = self.replace_letters_with_asterisks(self.password)
            url_hidden_password = f" {self.protocol}://{self.user}:{hidden_password}@{self.ip}:{self.port}/{self.stream_path} "
            self.update_status_bar('Streaming stopped', url_hidden_password, f'{self.video_resolution}')
        else:
            # Using new multi-camera system
            camera_count = len(cameras)
            if camera_count == 0:
                self.update_status_bar('Ready - No cameras configured', "Click Settings to add cameras", "")
            else:
                self.update_status_bar('Ready', "Select a camera to control", "")

        # Create the loading animation (legacy)
        self.loading_animation = LoadingAnimation(self,
                                                  "/images/Spinner-1s-104px.gif",
                                                  (104, 104))

        # Create an instance of the RTSPCameraStream class (legacy - for backward compatibility)
        self.rtspCameraStream = StreamThread(self.url, self.video_resolution, "")
        self.rtspCameraStream.first_frame_received.connect(lambda camera_id: self.setup_widgets_when_playing())
        self.rtspCameraStream.frame_received.connect(lambda camera_id, frame: self.display_frame(frame))
        self.rtspCameraStream.finished.connect(self.setup_widgets_when_stopped)
        self.rtspCameraStream.error_signal.connect(lambda camera_id, error: self.error_streaming(error))
        self.rtspCameraStream.status_signal.connect(lambda camera_id, status: self.streaming_status(status))

    def init_gui(self) -> None:
        """Initialize and set up the graphical user interface."""

        # Create central_widget as main container
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main vertical layout
        main_vertical_layout = QVBoxLayout(central_widget)
        main_vertical_layout.setContentsMargins(0, 0, 0, 0)
        main_vertical_layout.setSpacing(0)
        
        # Create TopNavigationBar instance
        self.top_nav_bar = TopNavigationBar()
        
        # Set up branding with application name
        logo_path = os.path.dirname(os.path.realpath(__file__)) + "/images/Security-Camera-icon.png"
        if os.path.exists(logo_path):
            self.top_nav_bar.set_branding(logo_path, "IP Camera Player")
        else:
            self.top_nav_bar.set_branding(None, "IP Camera Player")
        
        # Add Settings button
        self.top_nav_bar.add_menu_button("Settings", self.open_camera_settings)
        
        # Add control buttons to top navigation bar and store references
        self.start_button = self.top_nav_bar.add_menu_button("Start", self.start_streaming)
        self.pause_button = self.top_nav_bar.add_menu_button("Pause", self.pause_streaming)
        self.take_snapshot_button = self.top_nav_bar.add_menu_button("Snapshot", self.take_snapshot)
        self.stop_button = self.top_nav_bar.add_menu_button("Stop", self.stop_streaming)
        
        # Set initial button states
        self.start_button.setEnabled(False)
        self.pause_button.setEnabled(False)
        self.take_snapshot_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        
        # Add TopNavigationBar to main vertical layout at top
        main_vertical_layout.addWidget(self.top_nav_bar)
        
        # Create horizontal layout for sidebar and content area
        h_layout = QHBoxLayout()
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(0)
        
        # Create LeftSidebar instance
        self.left_sidebar = LeftSidebar()
        
        # Create CameraTreeView and add to sidebar
        self.camera_tree_view = CameraTreeView(self.camera_manager)
        self.left_sidebar.set_tree_view(self.camera_tree_view)
        
        # Connect tree view signals to handlers
        self.camera_tree_view.camera_selected.connect(self.handle_tree_camera_selection)
        self.camera_tree_view.camera_double_clicked.connect(self.handle_tree_camera_double_click)
        
        # Connect collapsed_changed signal
        self.left_sidebar.collapsed_changed.connect(self.handle_sidebar_collapse)
        
        # Add LeftSidebar to horizontal layout
        h_layout.addWidget(self.left_sidebar)
        
        # Create content area widget
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # Add camera grid container to content area (fills entire space now)
        content_layout.addWidget(self.camera_grid_container)
        
        # Add content widget to horizontal layout with stretch
        h_layout.addWidget(content_widget, 1)
        
        # Add horizontal layout to main vertical layout
        main_vertical_layout.addLayout(h_layout)

        #
        self.start_button.setFocus()

        # Set window properties
        self.setMinimumSize(720, 720)  # self.setMinimumSize(1280, 720)
        self.setWindowTitle("IP Camera Player")
        file_name = os.path.dirname(os.path.realpath(__file__)) + "\\images\\Security-Camera-icon.png"
        if path.exists(file_name):
            self.setWindowIcon(QIcon(file_name))
        self.setStatusBar(self.create_status_bar())
        
        # Connect CameraManager signals to UI updates
        self.camera_manager.camera_added.connect(self._on_camera_added)
        self.camera_manager.camera_removed.connect(self._on_camera_removed)
        self.camera_manager.cameras_reordered.connect(self._on_cameras_reordered)
        self.camera_manager.selection_changed.connect(self._on_selection_changed)
        
        # Load cameras from settings and create panels
        load_success = self.camera_manager.load_from_settings()
        
        # Notify user if settings load failed
        if not load_success:
            print("Warning: Failed to load camera settings, starting with empty configuration")
            # We don't show a message box here to avoid blocking startup
            # The error is logged to console for debugging
        
        cameras = self.camera_manager.get_all_cameras()
        for camera in cameras:
            self.create_camera_panel(camera)
        
        # Refresh tree view to show loaded cameras
        self.camera_tree_view.refresh_tree()
        
        # Update control buttons based on initial state
        self.update_control_buttons()
        
        # Apply professional dark theme styling
        self.apply_dark_theme()

    def create_status_bar(self) -> QStatusBar:
        # Create an instance of the QHBoxLayout class
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 2, 0, 2)
        layout.addSpacing(5)
        layout.addWidget(self.status_bar_message_label)
        layout.addSpacing(5)
        layout.addWidget(self.status_bar_url)
        layout.addSpacing(5)
        layout.addWidget(self.status_bar_resolution)
        layout.addSpacing(5)

        # Create an instance of the QWidget class
        container = QWidget()
        container.setLayout(layout)

        # Create an instance of the QStatusBar class
        status_bar = QStatusBar()
        status_bar.addWidget(container)
        status_bar.addWidget(QLabel(''), stretch=20)
        status_bar.addWidget(QLabel(f' SW Rev: {SW_VERSION} '))

        return status_bar

    def update_status_bar(self, message: str, url: str, res: str) -> None:
        """
        Update the status bar with new information for multi-camera context.

        Args:
            message: Status message to display
            url: Camera URL to display
            res: Resolution information to display
        """
        # Get camera count for multi-camera context
        camera_count = len(self.camera_manager.get_all_cameras())
        
        # Update message with camera count context
        if message:
            if camera_count > 0:
                self.status_bar_message_label.setText(f'Status: {message} | Cameras: {camera_count}')
            else:
                self.status_bar_message_label.setText(f'Status: {message}')
        
        if url:
            self.status_bar_url.setText(f'URL: {url}')
        
        if res:
            self.status_bar_resolution.setText(f'Resolution: {res}')

    @staticmethod
    def replace_letters_with_asterisks(input_string: str) -> str:
        # Replace each letter with '*', keeping non-letters intact
        return ''.join('*' for char in input_string)

    def start_streaming(self) -> None:
        """Start streaming for the selected camera only."""
        selected_camera = self.camera_manager.get_selected_camera()
        
        if selected_camera is None:
            return
        
        # Set resolution to 320x180 for streaming
        selected_camera.resolution = (640, 360)
        
        # Show loading animation for this camera
        if selected_camera.id in self.camera_panels:
            panel = self.camera_panels[selected_camera.id]
            panel.accepting_frames = True  # Enable frame acceptance
            panel.set_loading(True)
            panel.set_error("")  # Clear any previous errors
        
        # Update tree view indicator to show starting (green)
        self.camera_tree_view.update_camera_state(selected_camera.id)
        
        # Start the camera stream
        selected_camera.start_stream()
        
        # Connect stream signals if not already connected
        if selected_camera.stream_thread:
            try:
                selected_camera.stream_thread.frame_received.connect(
                    lambda camera_id, frame: self._on_frame_received(camera_id, frame)
                )
                selected_camera.stream_thread.error_signal.connect(
                    lambda camera_id, error: self._on_camera_error(camera_id, error)
                )
                selected_camera.stream_thread.first_frame_received.connect(
                    lambda camera_id: self._on_first_frame(camera_id)
                )
            except TypeError:
                # Signals may already be connected
                pass
        
        # Update control buttons
        self.update_control_buttons()

    def display_frame(self, frame: np.ndarray) -> None:
        if self.rtspCameraStream:
            # Store the frame for snapshot and zoom functionality
            self.current_frame = frame
            # Convert the frame to RGB format.
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            # Extract the height, width, and the number of channels.
            h, w, ch = frame.shape
            # Calculate bytes per line
            bytes_per_line = ch * w
            # Create an image in Qt format using the given frame.
            q_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
            # Create a pixmap from image.
            pixmap = QPixmap.fromImage(q_image)

            # Apply zoom factor to the pixmap, converting dimensions to integers
            self.scaled_width = int(self.zoom_factor * w)
            self.scaled_height = int(self.zoom_factor * h)

            # Scale the pixmap with integer dimensions and keep the aspect ratio
            scaled_pixmap = pixmap.scaled(self.scaled_width, self.scaled_height, Qt.KeepAspectRatio)

            # Enforce boundary limits for panning (do not pan outside the image)
            self.x_offset = max(0, min(self.x_offset, self.scaled_width - self.video_label.width()))
            self.y_offset = max(0, min(self.y_offset, self.scaled_height - self.video_label.height()))

            # Create a sub-area based on panning
            visible_pixmap = scaled_pixmap.copy(self.x_offset, self.y_offset, self.video_label.width(),
                                                self.video_label.height())

            # Display the frame
            self.video_label.setPixmap(visible_pixmap)

    def stop_streaming(self) -> None:
        """Stop streaming for the selected camera only."""
        selected_camera = self.camera_manager.get_selected_camera()
        
        if selected_camera is None:
            return
        
        # Disable frame acceptance before stopping stream to prevent race condition
        if selected_camera.id in self.camera_panels:
            self.camera_panels[selected_camera.id].accepting_frames = False
        
        # Stop the camera stream
        selected_camera.stop_stream()
        
        # Clear the panel display and show offline image
        if selected_camera.id in self.camera_panels:
            panel = self.camera_panels[selected_camera.id]
            panel.set_loading(False)
            # Clearing error will also show offline image
            panel.set_error("")
        
        # Update tree view indicator to show offline (red)
        self.camera_tree_view.update_camera_state(selected_camera.id)
        
        # Update control buttons
        self.update_control_buttons()
        self.start_button.setFocus()

    def pause_streaming(self) -> None:
        """Pause/unpause streaming for the selected camera only."""
        selected_camera = self.camera_manager.get_selected_camera()
        
        if selected_camera is None:
            return
        
        # Toggle pause state
        if selected_camera.state == CameraState.PAUSED:
            # Unpause
            self.pause_button.setText("Pause")
            selected_camera.pause_stream(False)
        else:
            # Pause
            self.pause_button.setText("Unpause")
            selected_camera.pause_stream(True)
        
        # Update control buttons
        self.update_control_buttons()

    def error_streaming(self, error: str) -> None:

        self.show_message_box("Stream Error",
                              error,
                              QMessageBox.Critical)

        self.update_status_bar(error, "", "")
        print(error)

    def streaming_status(self, status: str) -> None:
        self.update_status_bar(status, "", "")
        print(status)

    def reset_video_label(self: 'Windows') -> None:
        """
        Reset the video label to a solid black background after clearing the video frame.
        """
        # Clear any existing pixmap
        self.video_label.clear()

        # Create a black QPixmap with the same size as the video label
        black_pixmap = QPixmap(self.video_label.size())
        black_pixmap.fill(Qt.black)

        # Set the black pixmap as the label's content
        self.video_label.setPixmap(black_pixmap)

        # Ensure the UI is updated immediately
        self.video_label.repaint()

    def set_video_label_to_gray(self: 'Windows') -> None:
        """
        Set the video label to a solid gray background after clearing the video frame.
        """
        # Clear any existing pixmap
        self.video_label.clear()

        # Create a black QPixmap with the same size as the video label
        black_pixmap = QPixmap(self.video_label.size())
        black_pixmap.fill(Qt.lightGray)

        # Set the black pixmap as the label's content
        self.video_label.setPixmap(black_pixmap)

        # Ensure the UI is updated immediately
        self.video_label.repaint()

    def enable_widgets(self, enable: bool) -> None:
        """
        Enable or disable all child widgets of a QMainWindow.

        This function iterates through all child widgets of the specified QMainWindow
        and sets their enabled state according to the 'enabled' parameter.

        Parameters:
        - enabled: bool. The state to set for the child widgets (True to enable, False to disable).

        Returns:
        None
        """
        for widget in self.findChildren(QWidget):
            if isinstance(widget, QWidget):  # Ensure it's a QWidget
                if enable:
                    widget.setEnabled(True)
                else:
                    widget.setEnabled(False)
        # Ensure the UI is updated immediately
        self.video_label.repaint()

    def setup_widgets_when_starting(self) -> None:
        # self.enable_widgets(False)  # disable all the widgets
        self.loading_animation.start()  # show the loading animation
        self.set_video_label_to_gray()
        self.open_cam_settings_button.setEnabled(False)
        self.start_button.setEnabled(False)
        self.pause_button.setEnabled(False)
        self.take_snapshot_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.pause_button.setText("Pause")
        print("Loading camera stream, please wait...")
        self.update_status_bar("Loading stream", "", "")

    def setup_widgets_when_playing(self) -> None:
        # self.enable_widgets(True)
        self.loading_animation.stop()  # hide the loading animation
        self.open_cam_settings_button.setEnabled(False)
        self.start_button.setEnabled(False)
        self.pause_button.setEnabled(True)
        self.take_snapshot_button.setEnabled(True)
        self.stop_button.setEnabled(True)
        self.stop_button.setFocus()
        print("Streaming running")
        self.update_status_bar("Streaming running", "", "")

    def setup_widgets_when_stopped(self) -> None:
        # self.enable_widgets(True)
        self.loading_animation.stop()  # stop the loading animation
        self.reset_video_label()
        self.open_cam_settings_button.setEnabled(True)
        self.start_button.setEnabled(True)
        self.pause_button.setEnabled(False)
        self.take_snapshot_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        self.pause_button.setText("Pause")
        self.start_button.setFocus()
        print("Streaming has stopped")
        self.update_status_bar("Streaming stopped", "", "")

    def take_snapshot_old_ok(self) -> None:
        """
        Take a snapshot of the current frame and save it to a file.
        The user will input a custom file name, and the code will concatenate the current date and time.
        """

        # QMutexLocker automatically locks and unlocks the mutex
        # to access the shared resource (self.current_frame)
        # locker = QMutexLocker(self.mutex)
        QMutexLocker(self.mutex)

        try:
            if self.current_frame is not None:
                # Get the current date and time in the format MM/DD/YYYY and 12-hour time with AM/PM
                current_time = datetime.now().strftime("%m-%d-%Y_%I-%M-%S%p")

                # Prompt the user for a file name without extension
                options = QFileDialog.Options()
                file_path, _ = QFileDialog.getSaveFileName(self, "Save Snapshot", "",
                                                           "Images (*.png *.jpg *.jpeg);;All Files (*)",
                                                           options=options)

                if file_path:
                    # Extract the base name and the directory from the file path
                    base_name = os.path.splitext(os.path.basename(file_path))[0]
                    save_dir = os.path.dirname(file_path)

                    # Concatenate the user-provided name with the current date and time
                    final_file_name = f"{base_name}_{current_time}.png"
                    final_path = os.path.join(save_dir, final_file_name)

                    # Save the current frame to the selected file path
                    cv2.imwrite(final_path, self.current_frame)
                    print(f"Snapshot saved to {final_path}")

                else:
                    print("Save operation was canceled.")
            else:
                print("No frame available for snapshot")

        finally:
            # No need to manually unlock the mutex as QMutexLocker will do this automatically
            pass

    def take_snapshot(self) -> None:
        """
        Take a snapshot of the selected camera's current visible frame
        (with zoom and panning applied) and save it to a file.
        """
        selected_camera = self.camera_manager.get_selected_camera()
        
        if selected_camera is None:
            return
        
        if selected_camera.id not in self.camera_panels:
            return
        
        panel = self.camera_panels[selected_camera.id]
        
        try:
            with QMutexLocker(self.mutex):
                # Get the pixmap from the selected camera's panel
                pixmap = panel.video_label.pixmap()
        finally:
            pass

        if pixmap is not None and not pixmap.isNull():
            try:
                # Get the currently visible pixmap (with zoom and panning applied)
                visible_pixmap = pixmap.copy()

                # Get the current date and time in the format MM/DD/YYYY and 12-hour time with AM/PM
                current_time = datetime.now().strftime("%m-%d-%Y_%I-%M-%S%p")

                # Prompt the user for a file name without extension
                options = QFileDialog.Options()
                file_path, _ = QFileDialog.getSaveFileName(
                    self, 
                    f"Save Snapshot - {selected_camera.name}", 
                    f"{selected_camera.name}_{current_time}",
                    "Images (*.png *.jpg *.jpeg);;All Files (*)",
                    options=options
                )

                if file_path:
                    # Extract the base name and the directory from the file path
                    base_name = os.path.splitext(os.path.basename(file_path))[0]
                    save_dir = os.path.dirname(file_path)

                    # Concatenate the user-provided name with the current date and time
                    final_file_name = f"{base_name}_{current_time}.png"
                    final_path = os.path.join(save_dir, final_file_name)

                    # Save the visible pixmap to the selected file path
                    if visible_pixmap.save(final_path, 'PNG'):
                        print(f"Snapshot saved to {final_path}")
                        self.update_status_bar(f"Snapshot saved: {selected_camera.name}", "", "")
                    else:
                        print("Failed to save snapshot.")
                else:
                    print("Save operation was canceled.")
            except Exception as e:
                print(f"An error occurred while saving the snapshot: {e}")
        else:
            print("No visible pixmap available for snapshot.")

    def open_camera_settings(self) -> None:
        """Open the multi-camera settings dialog."""
        # Create an instance of the CameraListWidget to manage cameras
        camera_list_widget = CameraListWidget(self.camera_manager, self)
        camera_list_widget.exec_()  # show the camera list dialog

    def update_camera_settings(self, camera_settings: dict) -> None:
        if camera_settings:  # if the dict is not empty
            # Update the camera settings
            self.protocol = camera_settings['Protocol']
            self.user = camera_settings['User Name']
            self.password = camera_settings['Password']
            self.ip = camera_settings['IP Address']
            self.port = int(camera_settings['Port Number'])
            self.stream_path = camera_settings['Stream Path']
            if camera_settings['Video Resolution'] == '1080p':
                self.video_resolution = (1920, 1080)
            elif camera_settings['Video Resolution'] == '720p':
                self.video_resolution = (1280, 720)
            elif camera_settings['Video Resolution'] == '480p':
                self.video_resolution = (640, 480)
            else:
                self.video_resolution = (1920, 1080)

            if self.ip:
                # Update the url.
                self.url = f"{self.protocol}://{self.user}:{self.password}@{self.ip}:{self.port}/{self.stream_path}"

                # Hide the password
                hidden_password = self.replace_letters_with_asterisks(self.password)

                # Update the url and the camera resolution in the status bar
                url_hidden_password = f' {self.protocol}://{self.user}:{hidden_password}@{self.ip}:{self.port}/{self.stream_path}'
                self.update_status_bar("", url_hidden_password, f'{self.video_resolution}')

                self.start_button.setEnabled(True)
            else:

                self.start_button.setEnabled(False)

                # code here for error
                pass

    def start_from_camera_settings(self, camera_settings: dict) -> None:
        if camera_settings:  # if the dict is not empty
            self.update_camera_settings(camera_settings)
            self.start_streaming()

    def show_message_box(self, title: str, message: str, icon: int) -> None:
        """
        Create a modal dialog to inform the user about something he needs to know.
        It can be an error, or an information, or a warning.
        :param title: Title for this dialog window.
        :param message: Message to shown to user.
        :param icon: Icon shown, must be: QMessageBox::NoIcon QMessageBox.Information, QMessageBox.Warning, QMessageBox.Critical
        :return: None
        """
        # Create an instance of the QMessageBox class to create a message window.
        msg_box = QMessageBox(self)
        msg_box.setIcon(icon)
        msg_box.setText(message)
        msg_box.setWindowTitle(title)
        msg_box.setStandardButtons(QMessageBox.Ok)
        # msg_box.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        # msg_box.buttonClicked.connect(msgButtonClick)
        return_value = msg_box.exec()
        if return_value == QMessageBox.Ok:
            pass

    def save_app_settings(self) -> None:
        # Save and persist the camera settings for next time
        self.app_settings.setValue('protocol', self.protocol)
        self.app_settings.setValue('user', self.user)
        self.app_settings.setValue('password', self.password)
        self.app_settings.setValue('ip', self.ip)
        self.app_settings.setValue('port', self.port)
        self.app_settings.setValue('stream_path', self.stream_path)
        # Convert tuple to string and persist it
        self.app_settings.setValue('video_resolution', str(self.video_resolution))
    
    def create_camera_panel(self, camera_instance: CameraInstance) -> None:
        """
        Create a camera panel for the given camera instance.
        
        Args:
            camera_instance: CameraInstance to create panel for
        """
        # Create the panel with camera_grid_container as parent
        panel = CameraPanel(camera_instance, self.camera_grid_container)
        
        # Connect panel signals to handlers
        panel.clicked.connect(self.handle_camera_selection)
        panel.double_clicked.connect(self.handle_fullscreen_toggle)
        panel.drop_requested.connect(self.handle_camera_reorder)
        panel.retry_requested.connect(self.handle_camera_retry)
        
        # Connect camera stream signals to panel
        if camera_instance.stream_thread:
            camera_instance.stream_thread.frame_received.connect(
                lambda camera_id, frame: self._on_frame_received(camera_id, frame)
            )
            camera_instance.stream_thread.error_signal.connect(
                lambda camera_id, error: self._on_camera_error(camera_id, error)
            )
            camera_instance.stream_thread.first_frame_received.connect(
                lambda camera_id: self._on_first_frame(camera_id)
            )
        
        # Add panel to layout
        from PyQt5.QtWidgets import QWidgetItem
        self.camera_grid_layout.addItem(QWidgetItem(panel))
        
        # Store panel reference
        self.camera_panels[camera_instance.id] = panel
        
        # Show the panel
        panel.show()
        
        # Refresh tree view to stay in sync with camera manager
        if hasattr(self, 'camera_tree_view') and self.camera_tree_view:
            self.camera_tree_view.refresh_tree()
    
    def remove_camera_panel(self, camera_id: str) -> None:
        """
        Remove the camera panel for the given camera ID.
        
        Args:
            camera_id: ID of camera to remove panel for
        """
        if camera_id not in self.camera_panels:
            return
        
        panel = self.camera_panels[camera_id]
        
        # Disconnect signals
        try:
            panel.clicked.disconnect()
            panel.double_clicked.disconnect()
            panel.drop_requested.disconnect()
        except TypeError:
            # Signals may not be connected
            pass
        
        # Remove from layout
        for i in range(self.camera_grid_layout.count()):
            item = self.camera_grid_layout.itemAt(i)
            if item and item.widget() == panel:
                self.camera_grid_layout.takeAt(i)
                break
        
        # Remove from dictionary
        del self.camera_panels[camera_id]
        
        # Delete the widget
        panel.deleteLater()
        
        # Refresh tree view to stay in sync with camera manager
        if hasattr(self, 'camera_tree_view') and self.camera_tree_view:
            self.camera_tree_view.refresh_tree()
    
    def _on_frame_received(self, camera_id: str, frame: np.ndarray) -> None:
        """
        Handle frame received from camera stream.
        
        Args:
            camera_id: ID of camera that sent the frame
            frame: Video frame as numpy array
        """
        if camera_id in self.camera_panels:
            panel = self.camera_panels[camera_id]
            panel.set_frame(frame)
            panel.set_loading(False)
    
    def _on_camera_error(self, camera_id: str, error: str) -> None:
        """
        Handle error from camera stream.
        
        Args:
            camera_id: ID of camera that encountered error
            error: Error message
        """
        if camera_id in self.camera_panels:
            panel = self.camera_panels[camera_id]
            panel.set_error(error)
            panel.set_loading(False)
        
        # Update tree view indicator to show offline (red)
        self.camera_tree_view.update_camera_state(camera_id)
    
    def _on_first_frame(self, camera_id: str) -> None:
        """
        Handle first frame received from camera stream.
        
        Args:
            camera_id: ID of camera that sent first frame
        """
        if camera_id in self.camera_panels:
            panel = self.camera_panels[camera_id]
            panel.set_loading(False)
            panel.set_error("")  # Clear any previous error on successful connection
        
        # Update tree view indicator to show online (green)
        self.camera_tree_view.update_camera_state(camera_id)
    
    def handle_camera_selection(self, camera_id: str) -> None:
        """
        Handle camera selection.
        
        Updates visual selection state of panels, updates CameraManager
        selected camera, and updates control button states.
        
        Args:
            camera_id: ID of camera to select
        """
        # Update CameraManager selected camera
        self.camera_manager.select_camera(camera_id)
        
        # Update visual selection state of all panels
        for cid, panel in self.camera_panels.items():
            panel.set_selected(cid == camera_id)
        
        # Update control button states
        self.update_control_buttons()
        
        # Update status bar with selected camera info
        camera = self.camera_manager.get_camera(camera_id)
        if camera:
            # Format status message with camera state
            state_text = camera.state.value.capitalize()
            status_msg = f"Selected: {camera.name} ({state_text})"
            
            # Format URL (hide password for security)
            if camera.username and camera.password:
                hidden_password = self.replace_letters_with_asterisks(camera.password)
                url_display = f"{camera.protocol}://{camera.username}:{hidden_password}@{camera.ip_address}:{camera.port}/{camera.stream_path}"
            else:
                url_display = f"{camera.protocol}://{camera.ip_address}:{camera.port}/{camera.stream_path}"
            
            self.update_status_bar(
                status_msg,
                url_display,
                f"{camera.resolution}"
            )
    
    def update_control_buttons(self) -> None:
        """
        Update control button states based on selected camera.
        
        Enables/disables buttons based on whether a camera is selected
        and the state of the selected camera.
        """
        selected_camera = self.camera_manager.get_selected_camera()
        
        if selected_camera is None:
            # No camera selected - disable all control buttons
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(False)
            self.pause_button.setEnabled(False)
            self.take_snapshot_button.setEnabled(False)
        else:
            # Camera selected - enable buttons based on state
            if selected_camera.state == CameraState.STOPPED:
                self.start_button.setEnabled(True)
                self.stop_button.setEnabled(False)
                self.pause_button.setEnabled(False)
                self.take_snapshot_button.setEnabled(False)
            elif selected_camera.state == CameraState.STARTING:
                self.start_button.setEnabled(False)
                self.stop_button.setEnabled(True)
                self.pause_button.setEnabled(False)
                self.take_snapshot_button.setEnabled(False)
            elif selected_camera.state == CameraState.RUNNING:
                self.start_button.setEnabled(False)
                self.stop_button.setEnabled(True)
                self.pause_button.setEnabled(True)
                self.take_snapshot_button.setEnabled(True)
            elif selected_camera.state == CameraState.PAUSED:
                self.start_button.setEnabled(False)
                self.stop_button.setEnabled(True)
                self.pause_button.setEnabled(True)
                self.take_snapshot_button.setEnabled(True)
            elif selected_camera.state == CameraState.ERROR:
                self.start_button.setEnabled(True)
                self.stop_button.setEnabled(False)
                self.pause_button.setEnabled(False)
                self.take_snapshot_button.setEnabled(False)
    
    def handle_fullscreen_toggle(self, camera_id: str) -> None:
        """
        Handle fullscreen toggle for a camera panel.
        
        Toggles between fullscreen mode for the specified camera and
        normal grid layout.
        
        Args:
            camera_id: ID of camera to toggle fullscreen for
        """
        if camera_id not in self.camera_panels:
            return
        
        panel = self.camera_panels[camera_id]
        
        # Check if this panel is currently in fullscreen
        if panel.is_fullscreen:
            # Exit fullscreen mode
            panel.exit_fullscreen()
            self.camera_grid_layout.clear_fullscreen()
        else:
            # Enter fullscreen mode
            panel.enter_fullscreen()
            
            # Find the layout item for this panel
            for i in range(self.camera_grid_layout.count()):
                item = self.camera_grid_layout.itemAt(i)
                if item and item.widget() == panel:
                    self.camera_grid_layout.set_fullscreen(item)
                    break
    
    def handle_camera_reorder(self, source_id: str, target_id: str) -> None:
        """
        Handle drag-and-drop reordering of cameras.
        
        Swaps the positions of two cameras in the grid and persists
        the new order.
        
        Args:
            source_id: ID of camera being dragged
            target_id: ID of camera being dropped onto
        """
        # Get camera instances
        cameras = self.camera_manager.get_all_cameras()
        
        # Find indices of source and target cameras
        source_index = -1
        target_index = -1
        
        for i, camera in enumerate(cameras):
            if camera.id == source_id:
                source_index = i
            if camera.id == target_id:
                target_index = i
        
        if source_index == -1 or target_index == -1:
            return
        
        # Reorder cameras in CameraManager
        # We need to move source to target position
        self.camera_manager.reorder_cameras(source_id, target_index)
        
        # Find layout items for source and target panels
        source_item_index = -1
        target_item_index = -1
        
        for i in range(self.camera_grid_layout.count()):
            item = self.camera_grid_layout.itemAt(i)
            if item and item.widget() == self.camera_panels.get(source_id):
                source_item_index = i
            if item and item.widget() == self.camera_panels.get(target_id):
                target_item_index = i
        
        # Swap items in layout
        if source_item_index != -1 and target_item_index != -1:
            self.camera_grid_layout.swap_items(source_item_index, target_item_index)
    
    def handle_camera_retry(self, camera_id: str) -> None:
        """
        Handle retry request for a camera that encountered an error.
        
        Clears the error state and attempts to restart the camera stream.
        
        Args:
            camera_id: ID of camera to retry
        """
        camera = self.camera_manager.get_camera(camera_id)
        
        if camera is None:
            return
        
        # Clear error state in panel
        if camera_id in self.camera_panels:
            panel = self.camera_panels[camera_id]
            panel.set_error("")
            panel.set_loading(True)
        
        # Stop any existing stream
        if camera.stream_thread and camera.stream_thread.isRunning():
            camera.stop_stream()
        
        # Clear error state in camera instance
        camera.error_message = ""
        camera.state = CameraState.STOPPED
        
        # Start the stream again
        camera.start_stream()
        
        # Connect stream signals if not already connected
        if camera.stream_thread:
            try:
                camera.stream_thread.frame_received.connect(
                    lambda cam_id, frame: self._on_frame_received(cam_id, frame)
                )
                camera.stream_thread.error_signal.connect(
                    lambda cam_id, error: self._on_camera_error(cam_id, error)
                )
                camera.stream_thread.first_frame_received.connect(
                    lambda cam_id: self._on_first_frame(cam_id)
                )
            except TypeError:
                # Signals may already be connected
                pass
    
    def _on_camera_added(self, camera_id: str) -> None:
        """
        Handle camera_added signal from CameraManager.
        
        Args:
            camera_id: ID of camera that was added
        """
        camera = self.camera_manager.get_camera(camera_id)
        if camera:
            self.create_camera_panel(camera)
            # Refresh tree view to show new camera
            self.camera_tree_view.refresh_tree()
    
    def _on_camera_removed(self, camera_id: str) -> None:
        """
        Handle camera_removed signal from CameraManager.
        
        Args:
            camera_id: ID of camera that was removed
        """
        self.remove_camera_panel(camera_id)
        # Refresh tree view to remove camera
        self.camera_tree_view.refresh_tree()
        self.update_control_buttons()
    
    def _on_cameras_reordered(self) -> None:
        """
        Handle cameras_reordered signal from CameraManager.
        
        Rebuilds the camera grid layout to reflect the new order.
        """
        # Clear all panels from layout
        while self.camera_grid_layout.count() > 0:
            item = self.camera_grid_layout.takeAt(0)
            if item:
                widget = item.widget()
                if widget:
                    widget.setParent(None)
        
        # Re-add panels in new order
        cameras = self.camera_manager.get_all_cameras()
        for camera in cameras:
            if camera.id in self.camera_panels:
                panel = self.camera_panels[camera.id]
                from PyQt5.QtWidgets import QWidgetItem
                self.camera_grid_layout.addItem(QWidgetItem(panel))
                panel.show()
        
        # Refresh tree view to reflect new order
        self.camera_tree_view.refresh_tree()
    
    def _on_selection_changed(self, camera_id: str) -> None:
        """
        Handle selection_changed signal from CameraManager.
        
        Args:
            camera_id: ID of camera that was selected
        """
        # Update visual selection state
        for cid, panel in self.camera_panels.items():
            panel.set_selected(cid == camera_id)
        
        # Update control buttons
        self.update_control_buttons()
        
        # Update status bar
        camera = self.camera_manager.get_camera(camera_id)
        if camera:
            # Format status message with camera state
            state_text = camera.state.value.capitalize()
            status_msg = f"Selected: {camera.name} ({state_text})"
            
            # Format URL (hide password for security)
            if camera.username and camera.password:
                hidden_password = self.replace_letters_with_asterisks(camera.password)
                url_display = f"{camera.protocol}://{camera.username}:{hidden_password}@{camera.ip_address}:{camera.port}/{camera.stream_path}"
            else:
                url_display = f"{camera.protocol}://{camera.ip_address}:{camera.port}/{camera.stream_path}"
            
            self.update_status_bar(
                status_msg,
                url_display,
                f"{camera.resolution}"
            )
    
    def handle_tree_camera_selection(self, camera_id: str) -> None:
        """
        Handle camera selection from tree view.
        
        Updates camera selection to sync with tree view selection.
        
        Args:
            camera_id: ID of camera selected in tree view
        """
        # Use existing handle_camera_selection method to maintain consistency
        self.handle_camera_selection(camera_id)
    
    def handle_tree_camera_double_click(self, camera_id: str) -> None:
        """
        Handle camera double-click from tree view.
        
        Toggles fullscreen mode for the double-clicked camera.
        
        Args:
            camera_id: ID of camera double-clicked in tree view
        """
        # First select the camera
        self.handle_camera_selection(camera_id)
        
        # Then toggle fullscreen
        self.handle_fullscreen_toggle(camera_id)
    
    def handle_sidebar_collapse(self, is_collapsed: bool) -> None:
        """
        Handle sidebar collapse/expand event.
        
        Updates layout when sidebar is collapsed or expanded.
        
        Args:
            is_collapsed: True if sidebar is collapsed, False if expanded
        """
        # The layout will automatically adjust due to the sidebar's width change
        # No additional action needed, but we can add logging if desired
        if is_collapsed:
            print("Sidebar collapsed")
        else:
            print("Sidebar expanded")
    
    def apply_dark_theme(self) -> None:
        """
        Apply professional dark theme styling to the application.
        
        Sets application-wide stylesheet with a professional dark color palette
        consistent with surveillance software. Applies to main window and all
        child widgets.
        
        Color Palette:
            - Background: #1E1E1E (dark gray)
            - Secondary Background: #2D2D2D (lighter gray)
            - Accent: #0078D7 (blue)
            - Text Primary: #FFFFFF (white)
            - Text Secondary: #CCCCCC (light gray)
            - Border: #3F3F3F (medium gray)
        """
        # Define the global dark theme stylesheet
        dark_theme_stylesheet = """
            /* Global application styling */
            QMainWindow {
                background-color: #1E1E1E;
                color: #FFFFFF;
            }
            
            QWidget {
                background-color: #1E1E1E;
                color: #FFFFFF;
            }
            
            /* Button styling */
            QPushButton {
                background-color: #2D2D2D;
                color: #FFFFFF;
                border: 1px solid #3F3F3F;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 13px;
                font-weight: 500;
            }
            
            QPushButton:hover {
                background-color: #3F3F3F;
                border: 1px solid #0078D7;
            }
            
            QPushButton:pressed {
                background-color: #0078D7;
                border: 1px solid #0078D7;
            }
            
            QPushButton:disabled {
                background-color: #1E1E1E;
                color: rgba(255, 255, 255, 0.5);
                border: 1px solid #2D2D2D;
            }
            
            /* Label styling */
            QLabel {
                background-color: transparent;
                color: #FFFFFF;
            }
            
            /* Line edit styling */
            QLineEdit {
                background-color: #2D2D2D;
                color: #FFFFFF;
                border: 1px solid #3F3F3F;
                padding: 6px;
                border-radius: 4px;
                selection-background-color: #0078D7;
            }
            
            QLineEdit:focus {
                border: 1px solid #0078D7;
            }
            
            /* Combo box styling */
            QComboBox {
                background-color: #2D2D2D;
                color: #FFFFFF;
                border: 1px solid #3F3F3F;
                padding: 6px;
                border-radius: 4px;
            }
            
            QComboBox:hover {
                border: 1px solid #0078D7;
            }
            
            QComboBox::drop-down {
                border: none;
                background-color: #3F3F3F;
                width: 20px;
            }
            
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 6px solid #FFFFFF;
                margin-right: 6px;
            }
            
            QComboBox QAbstractItemView {
                background-color: #2D2D2D;
                color: #FFFFFF;
                border: 1px solid #3F3F3F;
                selection-background-color: #0078D7;
            }
            
            /* List widget styling */
            QListWidget {
                background-color: #2D2D2D;
                color: #FFFFFF;
                border: 1px solid #3F3F3F;
                border-radius: 4px;
            }
            
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #3F3F3F;
            }
            
            QListWidget::item:selected {
                background-color: rgba(0, 120, 215, 0.3);
                color: #FFFFFF;
            }
            
            QListWidget::item:hover {
                background-color: #3F3F3F;
            }
            
            /* Tree widget styling */
            QTreeWidget {
                background-color: #252525;
                color: #FFFFFF;
                border: none;
                outline: none;
            }
            
            QTreeWidget::item {
                padding: 6px;
                border: none;
            }
            
            QTreeWidget::item:selected {
                background-color: rgba(0, 120, 215, 0.3);
                color: #FFFFFF;
            }
            
            QTreeWidget::item:hover {
                background-color: #3F3F3F;
            }
            
            QTreeWidget::branch {
                background-color: #252525;
            }
            
            /* Dialog styling */
            QDialog {
                background-color: #1E1E1E;
                color: #FFFFFF;
            }
            
            /* Status bar styling */
            QStatusBar {
                background-color: #2D2D2D;
                color: #CCCCCC;
                border-top: 1px solid #3F3F3F;
            }
            
            QStatusBar QLabel {
                color: #CCCCCC;
            }
            
            /* Scroll bar styling */
            QScrollBar:vertical {
                background-color: #1E1E1E;
                width: 12px;
                border: none;
            }
            
            QScrollBar::handle:vertical {
                background-color: #3F3F3F;
                border-radius: 6px;
                min-height: 20px;
            }
            
            QScrollBar::handle:vertical:hover {
                background-color: #0078D7;
            }
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            
            QScrollBar:horizontal {
                background-color: #1E1E1E;
                height: 12px;
                border: none;
            }
            
            QScrollBar::handle:horizontal {
                background-color: #3F3F3F;
                border-radius: 6px;
                min-width: 20px;
            }
            
            QScrollBar::handle:horizontal:hover {
                background-color: #0078D7;
            }
            
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
        """
        
        # Apply the stylesheet to the application
        self.setStyleSheet(dark_theme_stylesheet)

    def wheelEvent(self, event: QWheelEvent) -> None:
        """
        Handle mouse wheel events to zoom in and out on the video stream.
        """
        # Adjust the zoom factor based on the mouse wheel scrolling
        if event.angleDelta().y() > 0:
            self.zoom_factor *= 1.1  # Zoom in
        else:
            self.zoom_factor /= 1.1  # Zoom out

        # Ensure zoom factor stays within a reasonable range
        self.zoom_factor = max(0.1, min(self.zoom_factor, 10))

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """
        Start panning when the mouse is pressed.
        """
        if event.button() == Qt.LeftButton:
            self.panning = True
            self.last_mouse_position = event.pos()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """
        Handle mouse movement for panning.
        """
        if self.panning:
            delta = event.pos() - self.last_mouse_position
            self.last_mouse_position = event.pos()

            # Update the offset for panning
            self.x_offset = max(0, min(self.x_offset - delta.x(), self.scaled_width - self.video_label.width()))
            self.y_offset = max(0, min(self.y_offset - delta.y(), self.scaled_height - self.video_label.height()))

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """
        Stop panning when the mouse is released.
        """
        if event.button() == Qt.LeftButton:
            self.panning = False

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        """Toggle full screen mode on mouse double click"""
        if self.is_full_screen:
            self.showNormal()  # Exit full screen mode
        else:
            self.showFullScreen()  # Enter full screen mode

        self.is_full_screen = not self.is_full_screen  # Toggle the state

    def closeEvent(self, event: QCloseEvent) -> None:
        """
        Handle application close event.
        
        Stops all camera streams, ensures all threads are properly terminated,
        and saves settings before closing.
        
        Args:
            event: Close event
        """
        # Stop all camera streams
        cameras = self.camera_manager.get_all_cameras()
        for camera in cameras:
            if camera.stream_thread and camera.stream_thread.isRunning():
                camera.stop_stream()
        
        # Stop loading animations in all panels
        for panel in self.camera_panels.values():
            panel.set_loading(False)
        
        # Save camera manager settings with error handling
        if not self.camera_manager.save_to_settings():
            # Log error but don't block closing
            print("Warning: Failed to save camera settings on application close")
            # Show a brief warning to user
            reply = QMessageBox.warning(
                self,
                "Storage Error",
                "Failed to save camera settings. Changes may be lost.\n\n"
                "Do you still want to close the application?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                event.ignore()
                return
        
        # Save old app settings for backward compatibility
        if self.app_settings:
            try:
                self.save_app_settings()
            except Exception as e:
                print(f"Warning: Failed to save legacy app settings: {e}")
        
        event.accept()


def main() -> None:
    """Main entry point for the application."""
    import signal
    
    # Enable Ctrl+C to work properly
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    
    app = QApplication(sys.argv)
    window = Windows()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
