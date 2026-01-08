# Smooth Resolution Transition - Architecture & Flow

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Windows (Main Application)               │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │        CameraManager                                  │  │
│  │  ┌─────────────────────────────────────────────────┐ │  │
│  │  │  CameraInstance (id, name, resolution, ...)     │ │  │
│  │  │  ┌──────────────────────────────────────────┐   │ │  │
│  │  │  │  StreamThread (640x360)                   │   │ │  │
│  │  │  │  - Reads frames continuously              │   │ │  │
│  │  │  │  - Emits frame_received signals          │   │ │  │
│  │  │  └──────────────────────────────────────────┘   │ │  │
│  │  │  ┌──────────────────────────────────────────┐   │ │  │
│  │  │  │  StreamThread (1920x1080) [NEW]          │   │ │  │
│  │  │  │  - Parallel connection during transition  │   │ │  │
│  │  │  │  - Emits first_frame_received on ready   │   │ │  │
│  │  │  └──────────────────────────────────────────┘   │ │  │
│  │  └─────────────────────────────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │        CameraPanel (Display Widget)                  │  │
│  │  - Shows frames from active StreamThread            │  │
│  │  - Handles user interactions (fullscreen, zoom)     │  │
│  │  - Calls change_resolution_smooth() on fullscreen   │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Resolution Transition Flow Diagram

### Entering Fullscreen (640x360 → 1920x1080)

```
Timeline:
─────────────────────────────────────────────────────────────────→ Time

User Action:
   │
   └─→ Double-click panel (enter fullscreen)
       │
       └─→ panel.enter_fullscreen()
       └─→ camera.change_resolution_smooth((1920, 1080))

OLD STREAM LIFECYCLE (640x360):
   ●─────────────────────────── ● ─────→ ✗
   │                            │
   Running                    Switch        Stopped
                            (on first
                          frame from
                          new stream)

NEW STREAM LIFECYCLE (1920x1080):
                  ● ─── ◐ ─── ◑ ─── ◒ ─── ● ─────────→
                  │                        │
                  │                    First Frame
                  Starting           Received
                                         │
                  NEW: Connecting     NEW: Active

DISPLAY OUTPUT:
   [Low Res]  [Low Res]  [Low Res] ⤳ [High Res]  [High Res]
      640x       640x       640x          1920x      1920x
      360        360        360           1080       1080
   │ ◀────────────────────────► │ ◀─────────────────────→ │
   │   Uninterrupted video     │  Higher resolution    │
   └─────────────────────────────────────────────────────┘
        NO BLACK SCREEN, NO INTERRUPTION
```

### Signal Flow During Transition

```
┌─────────────────────────────────────────────────────────────┐
│ Double-click Camera Panel (enter fullscreen)                │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ handle_fullscreen_toggle(camera_id)                         │
│  - panel.enter_fullscreen()                                 │
│  - camera_grid_layout.set_fullscreen(item)                  │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ camera.change_resolution_smooth((1920, 1080))              │
│  - Store old_stream_thread                                  │
│  - Create new_stream_thread (1920x1080)                    │
│  - Connect signals:                                         │
│    • new_stream_thread.first_frame_received → on_ready      │
│    • new_stream_thread.error_signal → _on_error            │
│  - Start new stream (old stream still running)             │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
        ▼                         ▼
    ┌──────────────┐         ┌──────────────┐
    │ Old Stream   │         │ New Stream   │
    │ (640x360)    │         │ (1920x1080)  │
    │ Continues    │         │ Connecting   │
    │ Running      │         │ Loading      │
    └──────────────┘         └─────┬────────┘
        │                          │
        │ Emits frame_received     │ Emits frame_received
        │ signals regularly        │ while loading
        │ (display shows these)    │
        │                          ▼
        │                    First frame
        │                    received!
        │                          │
        └──────────┬───────────────┘
                   │
                   ▼
    ┌────────────────────────────────┐
    │ on_new_stream_ready() callback │
    │  - Switch display stream       │
    │  - new_stream_thread becomes  │
    │    active                      │
    │  - Disconnect old_stream       │
    │    signals                     │
    │  - Stop old_stream_thread      │
    │  - Update resolution           │
    │  - Call user callback          │
    └────────────────────────────────┘
```

## Code Sequence Diagram

```
User              Windows            CameraInstance      StreamThreads       Display
 │                  │                      │              │  (Old)  (New)      │
 │ Double-click     │                      │              │                    │
 ├─────────────────→│                      │              │                    │
 │                  │ handle_fullscreen()  │              │                    │
 │                  ├─────────────────────→│              │                    │
 │                  │                      │ create new   │                    │
 │                  │                      │ StreamThread │                    │
 │                  │ enter_fullscreen()   ├──────────────┤                    │
 │                  │<─────────────────────┤              │                    │
 │                  │ change_resolution()  │              │                    │
 │                  │<─────────────────────┤              │                    │
 │                  │                      │ start new    │                    │
 │                  │                      │ thread       ├──→ Connecting...   │
 │                  │                      │ (old: running)│                   │
 │                  │                      │              │ Old: Frames →────────→
 │                  │                      │              │                    │
 │                  │                      │              │ New: Loading...    │
 │                  │                      │              │ (connecting to     │
 │                  │                      │              │  camera)           │
 │                  │                      │              │                    │
 │                  │                      │              │ ✓ Connected!       │
 │                  │                      │              │ ✓ First frame!     │
 │                  │                      │              │                    │
 │                  │<─────first_frame_signal sent────────┤                    │
 │                  │                      │              │                    │
 │                  │ on_ready callback()  │              │                    │
 │                  ├─────────────────────→│              │                    │
 │                  │ switch_stream        │              │                    │
 │                  │ stop_old_stream      │ stop old     │                    │
 │                  │ resolution=new       ├──────→ Stop──┤                    │
 │                  │                      │              │ Old: Stopped ✗     │
 │                  │<─────────────────────┤              │ New: Frames →────────→
 │                  │ update_status_bar()  │              │                    │
 │                  │                      │              │                    │
 │ [Continue viewing uninterrupted video at new resolution]                    │
 │                  │                      │              │                    │

Legend:
→ = Signal/Message passing
✓ = Successful state
✗ = Stopped/Ended state
```

## State Machine Diagram

```
                    ┌─────────────────────┐
                    │      STOPPED        │
                    │  (No stream running)│
                    └──────────┬──────────┘
                               │
                        start_streaming()
                               │
                               ▼
                    ┌─────────────────────┐
                    │     STARTING        │
                    │ (Waiting to connect)│
                    └──────────┬──────────┘
                               │
                    ┌──────────┴─────────────────────────┐
                    │                                    │
            (first_frame received)            (error or timeout)
                    │                                    │
                    ▼                                    ▼
        ┌──────────────────────┐          ┌──────────────────────┐
        │  RUNNING             │          │  ERROR               │
        │  (Streaming frames)  │          │  (Failed to connect) │
        └────────┬─────────────┘          └──────────┬───────────┘
                 │                                   │
         ┌───────┼───────────────────────────────┬───┘
         │       │                               │
    pause_stream() change_resolution_smooth()  stop_stream()
         │       │                               │
         ▼       │                               ▼
    ┌────────┐   │                       ┌─────────────┐
    │ PAUSED │   │                       │   STOPPED   │
    └────┬───┘   │                       └─────────────┘
         │       │
    unpause_stream()
         │       │
         ▼       │ [NEW] Parallel Stream Transition:
    ┌────────┐   │  1. Create new StreamThread
    │ RUNNING│   │  2. Start new thread (old continues)
    └────────┘   │  3. Wait for new → first_frame
                 │  4. Switch display
                 │  5. Disconnect & stop old
                 │  6. New becomes active
                 │
                 └──→ [Seamless Resolution Change]
```

## Frame Flow Diagram During Transition

### Before Transition (Single Stream)
```
Camera → Old StreamThread (640x360) → Frame Queue → Panel Display
         ↓
         Emits: frame_received(camera_id, frame)
                  ↓
                 CameraPanel.set_frame(frame)
                  ↓
                 Display (640x360)
```

### During Transition (Parallel Streams)
```
Camera ┬→ Old StreamThread (640x360) → Frame Queue ┐
       │                                             ├→ Panel Display
       │                                             │  (640x360 frames
       └→ New StreamThread (1920x1080) → Buffering ┘  until switch)
         (Building up frames, not displayed yet)

On first_frame from New:
  Switch display source
Camera ┬→ Old StreamThread (640x360) → Disconnecting
       │
       └→ New StreamThread (1920x1080) → Frame Queue → Panel Display
                                                       (1920x1080 frames)
```

### After Transition (Single Stream)
```
Camera → New StreamThread (1920x1080) → Frame Queue → Panel Display
         ↓
         Emits: frame_received(camera_id, frame)
                  ↓
                 CameraPanel.set_frame(frame)
                  ↓
                 Display (1920x1080)
```

## Key Implementation Points

### 1. **Closure Capture** in `on_new_stream_ready()`
```python
def on_new_stream_ready(camera_id: str) -> None:
    # Has access to:
    # - old_stream_thread (from enclosing scope)
    # - new_stream_thread (from enclosing scope)
    # - self (CameraInstance)
    # - on_ready_callback (from enclosing scope)
```

### 2. **Signal Thread Safety**
```python
# Signals are safely emitted from StreamThread
# (QThread subclass) and handled in main thread
new_stream_thread.first_frame_received.connect(
    on_new_stream_ready  # Handled in main thread
)
```

### 3. **Resource Cleanup**
```python
# Proper disconnection prevents memory leaks
try:
    old_stream_thread.first_frame_received.disconnect()
    old_stream_thread.error_signal.disconnect()
    old_stream_thread.frame_received.disconnect()
except (TypeError, RuntimeError):
    pass  # Already disconnected or not connected
```

### 4. **Error Handling**
```python
# If new stream fails to connect:
# - Old stream continues running
# - User sees uninterrupted video
# - Error logged via on_error callback
new_stream_thread.error_signal.connect(self._on_error)
```

## Timing Considerations

### Typical Sequence Timing

| Phase | Duration | Notes |
|-------|----------|-------|
| User double-click → function call | ~1-10ms | Immediate UI response |
| New stream creation | ~0-5ms | Thread object creation |
| New stream connection | 1-5s | Depends on network/camera |
| First frame received | +500ms-3s | From connection start |
| Display switch | ~16ms | Next screen refresh |
| Old stream cleanup | ~100-500ms | Thread termination |
| **Total time to HD** | **1-5 seconds** | From click to full HD display |

## Performance Characteristics

### Memory Usage
- **Before**: 1 StreamThread × ~5-20MB = ~5-20MB
- **During Transition**: 2 StreamThreads = ~10-40MB (+5-20MB)
- **After**: 1 StreamThread × ~5-20MB = ~5-20MB

### Network Bandwidth
- **Before**: ~500-3000 Kbps (low-res stream)
- **During**: ~500-3000 + ~2000-10000 Kbps = ~2500-13000 Kbps (both streams)
- **After**: ~2000-10000 Kbps (high-res stream)

### CPU Impact
- **Before**: ~10-20% (single stream decode + render)
- **During**: ~15-30% (dual stream decode, single render)
- **After**: ~20-30% (high-res stream)

## Quality Metrics

### User Experience
- ✅ **Continuity**: Zero frame drops during transition
- ✅ **Responsiveness**: Smooth resolution increase
- ✅ **Reliability**: Fallback to low-res on failure
- ✅ **Transparency**: No user awareness of parallel streams

### System Efficiency
- ⚠️ **Resource Overhead**: ~2x during transition (1-5 seconds)
- ⚠️ **Bandwidth Usage**: Temporary 2x spike
- ✅ **CPU Efficiency**: Minimal additional load
- ✅ **Memory Recovery**: Quick cleanup after transition
