# Implementation Plan

- [x] 1. Create data model classes for camera management
  - [x] 1.1 Implement CameraState enumeration
    - Define enum with states: STOPPED, STARTING, RUNNING, PAUSED, ERROR
    - _Requirements: 8.1, 8.2, 8.3, 8.5_

  - [x] 1.2 Implement CameraInstance class
    - Create class with all configuration attributes (id, name, protocol, username, password, ip_address, port, stream_path, resolution)
    - Implement to_dict() and from_dict() methods for serialization
    - Implement get_url() method to construct RTSP URL
    - Add state management attributes (state, error_message, stream_thread)
    - _Requirements: 1.3, 1.5, 9.1, 9.2_

  - [ ]* 1.3 Write property test for camera configuration serialization
    - **Property 1: Camera addition persistence**
    - **Property 25: Configuration persistence round-trip**
    - **Validates: Requirements 1.3, 1.5, 9.1, 9.2**

  - [x] 1.4 Implement CameraManager class
    - Create class with cameras list and QSettings integration
    - Implement add_camera(), remove_camera(), get_camera(), get_all_cameras() methods
    - Implement reorder_cameras() method
    - Implement select_camera() and get_selected_camera() methods
    - Implement save_to_settings() and load_from_settings() methods
    - Define signals: camera_added, camera_removed, camera_updated, cameras_reordered, selection_changed
    - _Requirements: 1.1, 1.3, 1.5, 2.2, 2.3, 4.4, 5.1, 9.1, 9.2, 9.3, 9.4_

  - [ ]* 1.5 Write property tests for CameraManager operations
    - **Property 2: Invalid camera rejection**
    - **Property 3: Camera deletion removes from list**
    - **Property 4: Deletion persistence**
    - **Property 11: Reorder persistence**
    - **Property 26: Order change persistence**
    - **Property 27: Add/delete persistence**
    - **Validates: Requirements 1.4, 2.2, 2.3, 4.4, 9.3, 9.4**

  - [x] 1.6 Implement settings migration logic
    - Create function to detect old single-camera settings format
    - Implement migration from old format to new multi-camera format
    - Preserve existing camera configuration as first camera
    - _Requirements: 9.2_

- [x] 2. Enhance StreamThread for multi-camera support
  - [x] 2.1 Add camera identification to StreamThread
    - Add camera_id attribute to StreamThread
    - Update signals to include camera_id where appropriate
    - Ensure thread cleanup is robust for multiple instances
    - _Requirements: 8.1, 8.2, 8.3_

  - [ ]* 2.2 Write property tests for stream thread state independence
    - **Property 22: Camera state independence**
    - **Validates: Requirements 8.1, 8.2, 8.3**

  - [x] 2.3 Implement per-camera stream control methods in CameraInstance
    - Implement start_stream() method
    - Implement stop_stream() method
    - Implement pause_stream(paused) method
    - Implement take_snapshot() method
    - Ensure proper thread lifecycle management
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 8.1, 8.2, 8.3_

  - [ ]* 2.4 Write property test for streaming camera deletion
    - **Property 5: Streaming camera deletion stops stream**
    - **Validates: Requirements 2.4**

- [x] 3. Create CameraPanel widget
  - [x] 3.1 Implement basic CameraPanel class
    - Create QWidget subclass with camera_instance attribute
    - Add video_label for video display
    - Add error_label for error messages
    - Integrate LoadingAnimation instance
    - Implement set_frame() method for video updates
    - _Requirements: 3.1, 3.4, 10.1, 10.2, 10.3_

  - [x] 3.2 Implement selection visual feedback
    - Add is_selected attribute
    - Override paintEvent() to draw selection border
    - Implement set_selected() method
    - Define clicked signal with camera_id
    - Override mousePressEvent() to emit clicked signal
    - _Requirements: 5.1, 5.2, 5.3_

  - [ ]* 3.3 Write property tests for camera selection
    - **Property 13: Camera selection updates state**
    - **Property 14: Selection switching**
    - **Property 15: Selection persistence**
    - **Property 16: Selected camera deletion clears selection**
    - **Validates: Requirements 5.1, 5.3, 5.4, 5.5**

  - [x] 3.3 Implement loading and error state display
    - Implement set_loading() method to show/hide loading animation
    - Implement set_error() method to display error messages
    - Position loading animation centered in panel
    - Style error label for visibility
    - _Requirements: 10.1, 10.2, 10.3, 10.4_

  - [ ]* 3.4 Write property tests for camera panel states
    - **Property 28: Loading animation during connection**
    - **Property 29: Successful connection hides loading**
    - **Property 30: Connection failure displays error**
    - **Property 31: Error isolation between cameras**
    - **Validates: Requirements 10.1, 10.2, 10.3, 10.4**

  - [x] 3.5 Implement zoom and pan functionality per panel
    - Add zoom_factor and pan_offset attributes
    - Override wheelEvent() for zoom control
    - Override mousePressEvent(), mouseMoveEvent(), mouseReleaseEvent() for panning
    - Update set_frame() to apply zoom and pan transformations
    - _Requirements: 6.4_

  - [x] 3.6 Implement fullscreen toggle
    - Add is_fullscreen attribute
    - Define double_clicked signal with camera_id
    - Override mouseDoubleClickEvent() to emit double_clicked signal
    - Implement enter_fullscreen() and exit_fullscreen() methods
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

  - [ ]* 3.7 Write property tests for fullscreen functionality
    - **Property 17: Fullscreen expansion**
    - **Property 18: Fullscreen hides other panels**
    - **Property 19: Fullscreen round-trip**
    - **Property 20: Fullscreen preserves zoom and pan**
    - **Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5**

  - [x] 3.8 Implement drag-and-drop support
    - Override mousePressEvent() to initiate drag with QDrag
    - Set drag data with camera_id
    - Override dragEnterEvent() and dragMoveEvent() to accept drops
    - Override dropEvent() to emit drop_requested signal
    - Provide visual feedback during drag operation
    - _Requirements: 4.1, 4.2, 4.3, 4.5_

  - [ ]* 3.9 Write property tests for drag-and-drop
    - **Property 10: Camera position swap**
    - **Property 12: Drag cancellation restores position**
    - **Validates: Requirements 4.3, 4.5**

- [x] 4. Implement CameraGridLayout
  - [x] 4.1 Create CameraGridLayout class
    - Create QLayout subclass
    - Implement addItem() and removeItem() methods
    - Add items list to track camera panels
    - _Requirements: 3.1, 3.2, 3.3_

  - [x] 4.2 Implement grid dimension calculation
    - Implement calculate_grid_dimensions(count) method
    - Use algorithm: prefer wider layouts, minimize wasted space
    - Handle edge cases (0, 1, 2 cameras)
    - _Requirements: 3.2_

  - [ ]* 4.3 Write property test for grid layout optimization
    - **Property 7: Grid layout optimization**
    - **Validates: Requirements 3.2**

  - [x] 4.4 Implement layout geometry calculation
    - Override setGeometry() to position all camera panels
    - Calculate panel sizes based on grid dimensions
    - Maintain aspect ratios
    - Handle window resizing
    - _Requirements: 3.2, 3.4, 3.5_

  - [ ]* 4.5 Write property tests for layout behavior
    - **Property 8: Dynamic layout recalculation**
    - **Property 9: Aspect ratio preservation**
    - **Validates: Requirements 3.3, 3.4**

  - [x] 4.6 Implement fullscreen mode in layout
    - Add fullscreen_item attribute
    - Implement set_fullscreen(item) method
    - Implement clear_fullscreen() method
    - Modify setGeometry() to handle fullscreen mode
    - _Requirements: 6.1, 6.2, 6.3, 6.5_

  - [x] 4.7 Implement item swapping for drag-and-drop
    - Implement swap_items(index1, index2) method
    - Update layout after swap
    - Trigger geometry recalculation
    - _Requirements: 4.3_

- [-] 5. Create camera configuration UI components
  - [x] 5.1 Implement CameraConfigDialog
    - Create QDialog subclass with form fields for all camera properties
    - Add fields: name, protocol, username, password, ip_address, port, stream_path, resolution
    - Implement load_camera() method to populate form
    - Implement get_camera_data() method to extract form data
    - Implement validate() method for form validation
    - Add save and cancel buttons
    - _Requirements: 1.2, 1.3, 1.4_

  - [ ]* 5.2 Write property test for configuration validation
    - **Property 2: Invalid camera rejection**
    - **Validates: Requirements 1.4**

  - [x] 5.3 Implement CameraListWidget dialog
    - Create QDialog subclass
    - Add QListWidget to display all cameras
    - Add buttons: add, edit, delete, close
    - Implement refresh_list() method
    - Implement show_camera_form() method
    - Connect to CameraManager signals
    - _Requirements: 1.1, 1.2, 2.1, 2.2_

  - [x] 5.4 Implement camera list item display
    - Display camera name and IP address in list
    - Show camera state icon (stopped, running, paused, error)
    - Enable/disable edit and delete buttons based on selection
    - _Requirements: 1.1, 2.1_

  - [x] 5.5 Implement add camera functionality
    - Handle add button click
    - Show CameraConfigDialog in add mode
    - Validate and add camera through CameraManager
    - Refresh list after addition
    - _Requirements: 1.2, 1.3, 1.5_

  - [x] 5.6 Implement edit camera functionality
    - Handle edit button click
    - Load selected camera into CameraConfigDialog
    - Validate and update camera through CameraManager
    - Refresh list after edit
    - _Requirements: 1.1_

  - [x] 5.7 Implement delete camera functionality
    - Handle delete button click
    - Confirm deletion with user
    - Delete camera through CameraManager
    - Refresh list after deletion
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [x] 6. Integrate multi-camera support into MainWindow
  - [x] 6.1 Refactor MainWindow initialization
    - Create CameraManager instance
    - Create CameraGridLayout instance
    - Replace single video_label with camera grid container
    - Initialize camera_panels dictionary
    - Load cameras from settings on startup
    - _Requirements: 3.1, 8.5, 9.2_

  - [ ]* 6.2 Write property tests for startup behavior
    - **Property 6: All cameras displayed on startup**
    - **Property 24: Startup initializes stopped state**
    - **Validates: Requirements 3.1, 8.5**

  - [x] 6.3 Implement camera panel creation and removal
    - Implement create_camera_panel(camera_instance) method
    - Implement remove_camera_panel(camera_id) method
    - Connect panel signals to handlers
    - Add/remove panels from grid layout
    - _Requirements: 1.3, 2.2, 3.1_

  - [x] 6.4 Implement camera selection handling
    - Implement handle_camera_selection(camera_id) method
    - Update visual selection state of panels
    - Update CameraManager selected camera
    - Update control button states
    - _Requirements: 5.1, 5.3, 5.4, 5.5, 7.5_

  - [x] 6.5 Implement fullscreen handling
    - Implement handle_fullscreen_toggle(camera_id) method
    - Call layout set_fullscreen() or clear_fullscreen()
    - Update panel fullscreen state
    - _Requirements: 6.1, 6.2, 6.3, 6.5_

  - [x] 6.6 Implement drag-and-drop reordering
    - Implement handle_camera_reorder(source_id, target_id) method
    - Call CameraManager reorder_cameras()
    - Update layout with new order
    - Persist new order
    - _Requirements: 4.1, 4.3, 4.4, 4.5_

  - [x] 6.7 Update control button handlers
    - Modify start_streaming() to operate on selected camera only
    - Modify stop_streaming() to operate on selected camera only
    - Modify pause_streaming() to operate on selected camera only
    - Modify take_snapshot() to operate on selected camera only
    - Implement update_control_buttons() to enable/disable based on selection
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

  - [ ]* 6.8 Write property tests for control operations
    - **Property 21: Control operates on selected camera only**
    - **Validates: Requirements 7.1, 7.2, 7.3, 7.4**

  - [x] 6.9 Update settings button handler
    - Modify open_camera_settings() to show CameraListWidget
    - Remove old single-camera settings dialog
    - _Requirements: 1.1, 1.2, 2.1, 2.2_

  - [x] 6.10 Implement application close handling
    - Override closeEvent() to stop all camera streams
    - Ensure all threads are properly terminated
    - Save settings before closing
    - _Requirements: 8.4, 9.1_

  - [ ]* 6.11 Write property tests for application lifecycle
    - **Property 23: Application close stops all streams**
    - **Validates: Requirements 8.4**

  - [x] 6.11 Connect CameraManager signals to UI updates
    - Connect camera_added signal to create_camera_panel
    - Connect camera_removed signal to remove_camera_panel
    - Connect cameras_reordered signal to layout update
    - Connect selection_changed signal to UI update
    - _Requirements: 1.3, 2.2, 4.4, 5.1_

- [x] 7. Implement error handling and user feedback
  - [x] 7.1 Implement per-camera error display
    - Update CameraPanel to show errors in panel
    - Display connection errors in specific camera panel
    - Display streaming errors in specific camera panel
    - Ensure errors don't affect other cameras
    - _Requirements: 10.3, 10.4_

  - [x] 7.2 Implement retry functionality
    - Add retry button to error display in CameraPanel
    - Implement retry logic to restart connection
    - Clear error state on successful retry
    - _Requirements: 10.5_

  - [ ]* 7.3 Write property test for error retry
    - **Property 32: Error retry capability**
    - **Validates: Requirements 10.5**

  - [x] 7.3 Implement configuration validation
    - Validate required fields in CameraConfigDialog
    - Display field-specific error messages
    - Prevent saving invalid configurations
    - _Requirements: 1.4_

  - [x] 7.4 Implement connection timeout handling
    - Set appropriate timeout for each camera connection
    - Display timeout errors in camera panel
    - Allow retry after timeout
    - _Requirements: 10.3_

  - [x] 7.5 Implement storage error handling
    - Handle QSettings read/write failures gracefully
    - Fallback to empty configuration if storage corrupted
    - Log storage errors
    - Notify user of persistence issues
    - _Requirements: 9.5_

- [x] 8. Implement security features
  - [x] 8.1 Implement password encryption
    - Encrypt passwords before saving to QSettings
    - Decrypt passwords when loading from QSettings
    - Use Qt's encryption or external library
    - _Requirements: 9.1, 9.2_

  - [x] 8.2 Implement secure credential handling
    - Mask password fields in UI
    - Clear password fields after use where appropriate
    - Never log passwords in plain text
    - _Requirements: 1.2_

- [x] 9. Update UI styling and polish
  - [x] 9.1 Style camera panel selection border
    - Define selection border color and width
    - Ensure visibility against various backgrounds
    - _Requirements: 5.2_

  - [x] 9.2 Style camera panel error display
    - Design error message appearance
    - Add error icon
    - Style retry button
    - _Requirements: 10.3, 10.4_

  - [x] 9.3 Style camera list widget
    - Design camera list item appearance
    - Add state icons (stopped, running, paused, error)
    - Style buttons consistently
    - _Requirements: 1.1_

  - [x] 9.4 Update status bar for multi-camera
    - Show selected camera info in status bar
    - Display camera count
    - Update status messages for multi-camera context
    - _Requirements: 5.1_

- [x] 10. Final integration and testing
  - [x] 10.1 Test complete workflow with multiple cameras
    - Add multiple cameras through settings
    - Start/stop/pause individual cameras
    - Test drag-and-drop reordering
    - Test fullscreen mode
    - Test selection switching
    - _Requirements: All_

  - [x] 10.2 Test settings persistence
    - Add cameras and restart application
    - Verify cameras are loaded correctly
    - Test order persistence
    - Test selection persistence
    - _Requirements: 9.1, 9.2, 9.3, 9.4_

  - [x] 10.3 Test error scenarios
    - Test with invalid camera credentials
    - Test with unreachable camera IPs
    - Test with network disconnection
    - Verify error isolation between cameras
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

  - [x] 10.4 Test performance with multiple streams
    - Test with 4, 9, and 16 simultaneous streams
    - Monitor CPU and memory usage
    - Verify UI responsiveness
    - Test on target hardware
    - _Requirements: 8.1, 8.2, 8.3_

  - [x] 10.5 Checkpoint - Ensure all tests pass
    - Ensure all tests pass, ask the user if questions arise.

- [x] 11. Implement TopNavigationBar component
  - [x] 11.1 Create TopNavigationBar widget class
    - Create QWidget subclass for top navigation bar
    - Set fixed height to 50px
    - Apply dark theme styling (#2D2D2D background)
    - Add bottom border (1px solid #3F3F3F)
    - _Requirements: 12.1, 12.5_

  - [x] 11.2 Add branding elements to navigation bar
    - Add QLabel for application logo/icon
    - Add QLabel for application title
    - Position branding elements on the left side
    - Style with white text, 16px bold font
    - _Requirements: 12.1_

  - [x] 11.3 Add menu buttons to navigation bar
    - Implement add_menu_button() method
    - Create menu buttons for key functions (Settings, View, Help)
    - Position menu buttons in center/right area
    - Apply flat button styling with hover effects
    - Connect menu buttons to corresponding actions
    - _Requirements: 12.2, 12.3_

  - [x] 11.4 Add status indicators to navigation bar
    - Implement add_status_indicator() and update_status() methods
    - Add status indicators for system information
    - Position status indicators on the right side
    - Style with secondary text color (#CCCCCC)
    - _Requirements: 12.4_

- [x] 12. Implement LeftSidebar component
  - [x] 12.1 Create LeftSidebar widget class
    - Create QWidget subclass for left sidebar
    - Set expanded width to 250px, collapsed width to 40px
    - Apply dark theme styling (#252525 background)
    - Add right border (1px solid #3F3F3F)
    - _Requirements: 11.1, 11.5_

  - [x] 12.2 Implement collapse/expand functionality
    - Add collapse button to sidebar
    - Implement toggle_collapse() method
    - Implement set_collapsed() method with animation
    - Emit collapsed_changed signal on state change
    - Update layout when collapsed/expanded
    - _Requirements: 11.5_

  - [x] 12.3 Integrate CameraTreeView into sidebar
    - Create container for tree view
    - Position tree view below collapse button
    - Ensure tree view fills available space
    - Handle visibility when sidebar is collapsed
    - _Requirements: 11.1_

- [x] 13. Implement CameraTreeView component
  - [x] 13.1 Create CameraTreeView widget class
    - Create QTreeWidget subclass for camera tree
    - Apply dark theme styling (#252525 background)
    - Set item height to 32px
    - Configure selection and hover styles
    - _Requirements: 11.1_

  - [x] 13.2 Implement tree structure with locations
    - Implement add_location() method to create location nodes
    - Implement add_camera_to_location() method
    - Create expandable/collapsible location nodes
    - Style location nodes distinctly from camera items
    - _Requirements: 11.2_

  - [x] 13.3 Implement camera item display
    - Display camera name in tree items
    - Add status icons based on camera state
    - Store camera ID in item data (Qt.UserRole)
    - Update item appearance based on camera state
    - _Requirements: 11.1_

  - [x] 13.4 Implement tree interaction handlers
    - Implement get_selected_camera_id() method
    - Implement select_camera() method
    - Handle single-click to emit camera_selected signal
    - Handle double-click to emit camera_double_clicked signal
    - _Requirements: 11.3, 11.4_

  - [x] 13.5 Implement tree refresh functionality
    - Implement refresh_tree() method
    - Load cameras from CameraManager
    - Group cameras by location
    - Preserve expansion state during refresh
    - _Requirements: 11.1, 11.2_

- [x] 14. Update CameraInstance to support location
  - [x] 14.1 Add location field to CameraInstance
    - Add location attribute to __init__
    - Update to_dict() to include location
    - Update from_dict() to load location
    - Set default location to "Default" if not specified
    - _Requirements: 11.2_

  - [x] 14.2 Update CameraConfigDialog to include location
    - Add location field to configuration form
    - Add QLineEdit for location input
    - Update load_camera() to populate location field
    - Update get_camera_data() to include location
    - Update validate() to handle location field
    - _Requirements: 11.2_

- [x] 15. Integrate new UI components into MainWindow
  - [x] 15.1 Refactor MainWindow layout structure
    - Create central_widget as main container
    - Create main_layout as QHBoxLayout
    - Remove old single-video layout
    - Position components: TopNavigationBar at top, LeftSidebar on left, camera grid in center
    - _Requirements: 11.1, 12.1_

  - [x] 15.2 Instantiate and add TopNavigationBar
    - Create TopNavigationBar instance
    - Add to main window layout at top
    - Set up branding with application name
    - Add menu buttons (Settings, View, Help)
    - Connect menu button signals to handlers
    - _Requirements: 12.1, 12.2, 12.3_

  - [x] 15.3 Instantiate and add LeftSidebar
    - Create LeftSidebar instance
    - Add to main_layout on left side
    - Get CameraTreeView reference
    - Connect tree view signals to handlers
    - Connect collapsed_changed signal
    - _Requirements: 11.1, 11.5_

  - [x] 15.4 Update camera grid container positioning
    - Ensure camera_grid_container is in main_layout
    - Set proper stretch factors for responsive layout
    - Ensure grid fills remaining space
    - _Requirements: 11.1_

  - [x] 15.5 Implement tree view integration handlers
    - Implement handle_tree_camera_selection() method
    - Implement handle_tree_camera_double_click() method
    - Implement handle_sidebar_collapse() method
    - Update camera selection to sync with tree view
    - _Requirements: 11.3, 11.4, 11.5_

  - [x] 15.6 Update camera panel creation to refresh tree
    - Modify create_camera_panel() to refresh tree view
    - Modify remove_camera_panel() to refresh tree view
    - Ensure tree view stays in sync with camera manager
    - _Requirements: 11.1_

- [x] 16. Apply professional dark theme styling
  - [x] 16.1 Implement apply_dark_theme() method
    - Create method to apply global dark theme
    - Set application-wide stylesheet
    - Define color palette (#1E1E1E, #2D2D2D, #0078D7, etc.)
    - Apply to main window and all child widgets
    - _Requirements: 13.2_

  - [x] 16.2 Update CameraPanel styling for minimal borders
    - Reduce border width to 1px
    - Use #2D2D2D for border color
    - Reduce spacing between panels to 2px
    - Update selection border to 3px solid #0078D7
    - Ensure black background (#000000)
    - _Requirements: 13.1, 13.3_

  - [x] 16.3 Update CameraGridLayout spacing
    - Set layout spacing to 2px
    - Set layout margins to 0px
    - Ensure minimal gaps between panels
    - _Requirements: 13.1, 13.5_

  - [x] 16.4 Update control buttons styling
    - Apply dark theme to all control buttons
    - Use #2D2D2D background
    - Use #3F3F3F for hover state
    - Use #0078D7 for active state
    - Update disabled state styling
    - _Requirements: 13.2_

  - [x] 16.5 Update dialog styling
    - Apply dark theme to CameraListWidget
    - Apply dark theme to CameraConfigDialog
    - Ensure consistent styling across all dialogs
    - Update text colors for readability
    - _Requirements: 13.2_

- [x] 17. Final UI integration and testing
  - [x] 17.1 Test new UI layout
    - Verify TopNavigationBar displays correctly
    - Verify LeftSidebar displays and collapses properly
    - Verify CameraTreeView shows cameras organized by location
    - Verify camera grid fills remaining space
    - Test window resizing behavior
    - _Requirements: 11.1, 11.5, 12.1_

  - [x] 17.2 Test tree view interactions
    - Test single-click camera selection in tree
    - Test double-click fullscreen from tree
    - Test location node expand/collapse
    - Verify tree stays in sync with camera changes
    - _Requirements: 11.2, 11.3, 11.4_

  - [x] 17.3 Test dark theme appearance
    - Verify all components use dark theme
    - Verify text is readable on dark backgrounds
    - Verify borders and spacing are minimal
    - Verify selection highlighting is visible
    - Compare appearance to reference image
    - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5_

  - [x] 17.4 Test menu bar functionality
    - Test Settings menu button opens camera settings
    - Test other menu buttons if implemented
    - Verify status indicators update correctly
    - _Requirements: 12.2, 12.3, 12.4_

  - [x] 17.5 Checkpoint - Ensure all UI tests pass
    - Ensure all tests pass, ask the user if questions arise.
