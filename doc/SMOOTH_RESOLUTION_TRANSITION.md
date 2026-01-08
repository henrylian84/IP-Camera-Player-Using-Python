# Smooth Resolution Transition Implementation

## Problem Statement
Previously, when switching resolutions (e.g., entering/exiting fullscreen mode), the application would:
1. Stop the current (low-resolution) stream immediately
2. Start a new stream with the new resolution
3. Wait for the new stream to connect and receive the first frame

This created a noticeable **interruption in the camera feed** for the user, as there was a gap between when the old stream disconnected and the new stream became available.

## Solution: Parallel Stream Switching

The new implementation uses a **parallel streaming approach** to eliminate the interruption:

### How It Works

1. **Keep Current Stream Running**: The existing low-resolution stream continues to run and display frames to the user
2. **Start New Stream in Background**: A second stream thread is created with the new (high) resolution
3. **Seamless Transition**: Once the new stream receives its first frame (indicating it's ready), the display switches to the new stream
4. **Cleanup**: The old stream thread is then safely stopped and cleaned up

### Key Benefits

- ✅ **No Interruption**: Users see continuous video - no black screen or gap
- ✅ **Smooth Experience**: Video smoothly transitions from low to high resolution (or vice versa)
- ✅ **Better Performance**: Leverages the camera's ability to support multiple simultaneous streams
- ✅ **Automatic Fallback**: If the new stream fails to connect, the old stream continues uninterrupted

## Implementation Details

### New Method: `CameraInstance.change_resolution_smooth()`

```python
def change_resolution_smooth(self, new_resolution: Tuple[int, int], on_ready_callback=None) -> None:
    """
    Change camera resolution smoothly without disconnecting the current stream.
    
    This method keeps the current low-resolution stream running while starting
    a new stream thread with the desired resolution in parallel. Once the new
    stream is ready (first frame received), it switches to the new stream and
    cleans up the old one.
    
    Args:
        new_resolution: Target resolution as (width, height) tuple
        on_ready_callback: Optional callback function to call when new stream is ready
                         Signature: callback(camera_id: str) -> None
    """
```

### Updated Method: `Windows.handle_fullscreen_toggle()`

The fullscreen toggle now uses the new smooth resolution change method:

**Before:**
```python
# Immediately stop the old stream and start a new one
camera.stop_stream()
camera.resolution = (1920, 1080)
camera.start_stream()
```

**After:**
```python
# Smoothly transition to new resolution while keeping old stream running
camera.change_resolution_smooth(
    (1920, 1080),
    on_ready_callback=lambda cam_id: self.update_status_bar("", "", f"{camera.resolution}")
)
```

## Technical Flow

### When Entering Fullscreen (640x360 → 1920x1080):

```
Time →

OLD STREAM (640x360):  Running → Running → Running → Stopping → Stopped
                       ↓        ↓        ↓
DISPLAY:           [Low Res] [Low Res] [High Res] [High Res]
                                ↑
NEW STREAM (1920x1080):         Starting → Loading → Ready → Running
```

The display stays on the low-resolution feed until the high-resolution stream sends its first frame, creating a seamless transition.

### Stream Thread Connection Sequence:

1. Old stream thread continues running normally
2. New stream thread created and started with target resolution
3. New stream connects to camera and begins receiving frames
4. New stream emits `first_frame_received` signal
5. **Switch point**: Display switches from old stream to new stream
6. Old stream is safely disconnected and cleaned up
7. New stream continues as the active stream

## Fallback Behavior

If the new stream fails to establish a connection:
- The old stream remains running and active
- User sees uninterrupted video at the previous resolution
- Error is logged, but user experience is not impacted
- Optional callback can be used to provide status feedback

## Configuration Notes

The implementation respects existing camera settings:
- **Connection Timeout**: Uses the camera's configured timeout (default: 20 seconds)
- **Authentication**: Uses existing credentials (RTSP URL constructed automatically)
- **Stream Path**: Uses configured stream path
- **Frame Throttling**: Maintains existing frame rate settings

## Testing Scenarios

To verify the smooth transition works correctly:

1. **Enter Fullscreen**:
   - Select a camera and start streaming at 640x360
   - Double-click the camera panel to enter fullscreen
   - Verify video continues uninterrupted while transitioning to 1920x1080

2. **Exit Fullscreen**:
   - While in fullscreen at 1920x1080, double-click again
   - Verify video continues uninterrupted while transitioning back to 640x360

3. **Slow Networks**:
   - On a slower network where high-resolution takes several seconds to load
   - Video should remain visible at low resolution until high resolution is ready
   - This is the primary benefit - no "loading" gap in the video

## Future Enhancements

This implementation could be extended to:
- Add a visual indicator when a resolution change is in progress
- Display "HD available" notification when high resolution becomes ready
- Allow users to manually trigger resolution changes from a UI button
- Implement adaptive bitrate selection based on network conditions
- Add support for switching between different stream variants (main, sub-stream)

## Migration Notes

This change is **backward compatible**:
- Old code using `camera.stop_stream()` + `camera.resolution = ...` + `camera.start_stream()` still works
- `change_resolution_smooth()` is a new method that doesn't affect existing functionality
- No configuration changes needed

## Performance Considerations

- **Memory**: Two stream threads may be active briefly during transition (temporary 2x resource usage)
- **Network**: Two streams consume ~2x bandwidth during transition period
- **CPU**: Minimal impact - one stream continues rendering while the other initializes
- **Duration**: Typically resolves in 1-5 seconds depending on network and camera
