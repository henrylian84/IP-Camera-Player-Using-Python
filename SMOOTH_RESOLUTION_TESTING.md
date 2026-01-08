# Testing Guide: Smooth Resolution Transition

## Quick Start

The smooth resolution transition feature is now active and will be used automatically when:
- **Entering fullscreen mode** (640x360 → 1920x1080): Double-click a camera panel
- **Exiting fullscreen mode** (1920x1080 → 640x360): Double-click fullscreen panel

## What to Observe

### Expected Behavior

1. **Before Transition**:
   - Camera streaming at current resolution (e.g., 640x360)
   - Video is smooth and continuous

2. **During Transition** (when entering fullscreen):
   - Video continues uninterrupted at 640x360
   - No black screen or "loading" pause
   - In the background, high-resolution stream (1920x1080) begins connecting

3. **After Transition** (when high-resolution ready):
   - Video smoothly switches to 1920x1080
   - Low-resolution stream is cleaned up
   - Video continues smoothly at higher resolution

### How to Verify It's Working

#### Test 1: Visual Continuity
1. Start a camera stream (should be at 640x360)
2. Watch the video for ~10 frames (note continuity)
3. Double-click to enter fullscreen
4. **Expected**: Video never stops, immediately switches to higher resolution within 1-5 seconds
5. **Problem would look like**: Video goes black for several seconds before appearing at high resolution

#### Test 2: Slow Network Simulation
1. Use developer tools or network throttling to slow down connection
2. Start camera stream at 640x360
3. Double-click fullscreen
4. **Expected**: Low-resolution video continues while high-resolution loads in background
5. **Problem would look like**: Screen goes black while waiting for high-resolution to load

#### Test 3: Exit Fullscreen
1. While in fullscreen at 1920x1080, double-click again
2. **Expected**: Video continues uninterrupted while switching back to 640x360
3. **Problem would look like**: Brief interruption or black screen

## Debug Output

Check the console for these informational messages:

```
Starting streaming
Streaming started
```

If there are issues, you'll see error messages like:
```
Error in resolution change callback: [error details]
```

## Technical Details

### Active Stream Management

The implementation maintains:
- **Old Stream**: Low-resolution thread continues running
- **New Stream**: High-resolution thread starts connecting
- **Display**: Shows old stream until new stream is ready
- **Switchover**: Happens on `first_frame_received` signal from new stream

### Fallback Behavior

If the high-resolution stream fails to connect:
- The low-resolution stream remains active
- User sees uninterrupted video
- Error is logged to console
- Display stays on low resolution (graceful degradation)

## Performance Notes

### Expected Resource Usage During Transition

- **Memory**: ~2x normal (two stream threads active briefly)
- **Network Bandwidth**: ~2x normal (two streams receiving frames)
- **CPU**: Minimal increase (one stream continues rendering)
- **Duration**: 1-5 seconds depending on network and camera

### After Transition Complete

Resource usage returns to normal (single stream running).

## Troubleshooting

### Issue: Video interrupts when changing resolution

**Solution**: Check camera configuration
- Verify camera supports multiple simultaneous streams
- Confirm network bandwidth is sufficient for 2x streaming during transition
- Check camera connection timeout settings

### Issue: High-resolution stream never appears

**Possible causes**:
- Camera may not support the requested resolution
- Network connectivity issue
- Camera timeout too short for high-resolution stream

**Solution**:
- Check camera specifications for supported resolutions
- Verify network connectivity
- Try increasing connection timeout in camera settings

### Issue: Old stream doesn't stop after transition

**Possible causes**:
- Callback error in signal disconnect
- Thread lifecycle issue

**Solution**:
- Check console for error messages
- Restart application
- Verify camera thread management

## Code Changes Summary

### Modified Files

- **ip_camera_player.py**:
  - Added `CameraInstance.change_resolution_smooth()` method
  - Updated `Windows.handle_fullscreen_toggle()` to use smooth transitions

### Key Differences from Previous Implementation

**Old Method** (immediate disconnect):
```python
camera.stop_stream()                    # Immediately disconnect
camera.resolution = (1920, 1080)
camera.start_stream()                   # Start new stream
# Result: Black screen until new stream connects
```

**New Method** (parallel streams):
```python
camera.change_resolution_smooth(        # Start new stream in background
    (1920, 1080),                       # Old stream continues
    on_ready_callback=...               # Switch when new stream ready
)
# Result: Uninterrupted video
```

## Monitoring

To monitor resolution changes in real-time:

1. Open browser developer console
2. Watch for status updates
3. Observe frame updates in the video display
4. Check console for any error messages

## Next Steps

To further optimize:
- Monitor actual resolution switch time
- Test with various camera types and network conditions
- Consider adding visual feedback (e.g., "HD Ready" indicator)
- Implement user-facing resolution selection UI
