# Motion Gate - Standalone Railway Inspection Script

A robust, standalone Python script for railway wagon inspection using DroidCam and OpenCV motion detection.

## Features

✅ **DroidCam Integration** - Reads video from mobile IP webcam  
✅ **Robust Motion Detection** - OpenCV Background Subtraction (MOG2)  
✅ **Motion Gate System** - IDLE until train detected, then ACTIVE  
✅ **Frame Capture** - Saves frames with timestamps when train present  
✅ **MIMO Integration Ready** - Clear placeholder for deblurring model  
✅ **Real-time Visualization** - Shows detection status and motion mask  
✅ **Configurable** - Easy tuning via config file  

---

## Quick Start

### 1. Test DroidCam Connection

```bash
python test_droidcam_connection.py
```

Update the IP address if needed, then verify you see the video feed.

### 2. Configure Settings

Edit `motion_gate_config.py`:

```python
# Your DroidCam IP (find it in the DroidCam app)
DROIDCAM_URL = "http://192.168.1.6:4747/video"

# Adjust sensitivity if needed
MOTION_THRESHOLD = 25.0  # Higher = less sensitive
MIN_CONTOUR_AREA = 8000  # Minimum object size
```

### 3. Run Motion Gate

```bash
python motion_gate_droidcam.py
```

**Controls:**
- Press `q` to quit
- Press `r` to reset background model

---

## How It Works

### Motion Gate States

```
┌──────────┐
│ LEARNING │ ← First 30 frames: Learning background
└────┬─────┘
     ↓
┌──────────┐
│   IDLE   │ ← Monitoring for motion (no capture)
└────┬─────┘
     ↓ Motion detected
┌──────────┐
│DETECTING │ ← Confirming train (15 consecutive frames)
└────┬─────┘
     ↓ Train confirmed
┌──────────┐
│  ACTIVE  │ ← Capturing frames + processing
└────┬─────┘
     ↓ No motion for 60 frames
┌──────────┐
│   IDLE   │ ← Train passed, waiting for next
└──────────┘
```

### Motion Detection Pipeline

1. **Background Subtraction** - MOG2 algorithm learns static background
2. **Shadow Removal** - Eliminates shadow false positives
3. **Noise Filtering** - Morphological operations (opening + closing)
4. **Contour Detection** - Find connected moving objects
5. **Size Filtering** - Only large objects (trains) trigger gate
6. **Motion Percentage** - Calculate % of frame with motion
7. **Threshold Check** - Must exceed 25% to be considered motion

### Key Parameters

| Parameter | Default | Effect |
|-----------|---------|--------|
| `MOTION_THRESHOLD` | 25% | % of pixels that must change |
| `MIN_CONTOUR_AREA` | 8000 | Minimum object size in pixels |
| `FRAMES_TO_CONFIRM_TRAIN` | 15 | Consecutive motion frames to activate |
| `FRAMES_NO_MOTION_TO_STOP` | 60 | No-motion frames to deactivate |
| `LEARNING_FRAMES` | 30 | Frames to learn background |
| `BG_VAR_THRESHOLD` | 50 | Background subtractor sensitivity |

---

## Output

### Folder Structure

```
motion_gate_output/
└── session_20251227_143055/
    └── frames/
        ├── frame_000001_143056_123456.jpg
        ├── frame_000002_143056_234567.jpg
        ├── frame_000003_143056_345678.jpg
        └── ...
```

Each frame is saved with:
- Sequential number
- Timestamp (HH:MM:SS_microseconds)

---

## Integrating Your MIMO Model

Find this section in `motion_gate_droidcam.py`:

```python
def process_active_frame(self, frame):
    """Process frame when in ACTIVE state."""
    
    # Save original frame
    if SAVE_FRAMES:
        cv2.imwrite(frame_path, frame)
    
    # ==========================================
    # TODO: INTEGRATE MIMO MODEL HERE
    # ==========================================
    # Example:
    # 1. Preprocess for MIMO
    #    frame_tensor = preprocess_for_mimo(frame)
    #
    # 2. Run deblurring
    #    deblurred = mimo_model(frame_tensor)
    #
    # 3. Post-process
    #    deblurred_frame = postprocess_mimo(deblurred)
    #
    # 4. Run OCR
    #    wagon_number = ocr_reader.readtext(deblurred_frame)
    #
    # 5. Save results
    #    cv2.imwrite(f"deblurred_{count}.jpg", deblurred_frame)
    # ==========================================
    
    return frame
```

Replace the TODO section with your existing MIMO deblurring code.

---

## Troubleshooting

### Problem: Too many false positives (capturing when no train)

**Solutions:**
```python
MOTION_THRESHOLD = 30.0  # Increase from 25
MIN_CONTOUR_AREA = 12000  # Increase from 8000
FRAMES_TO_CONFIRM_TRAIN = 20  # Increase from 15
BG_VAR_THRESHOLD = 70  # Increase from 50
```

### Problem: Missing trains (not detecting)

**Solutions:**
```python
MOTION_THRESHOLD = 18.0  # Decrease from 25
MIN_CONTOUR_AREA = 5000  # Decrease from 8000
FRAMES_TO_CONFIRM_TRAIN = 10  # Decrease from 15
BG_VAR_THRESHOLD = 35  # Decrease from 50
```

### Problem: Recording stops too early (during train)

**Solutions:**
```python
FRAMES_NO_MOTION_TO_STOP = 90  # Increase from 60
MOTION_THRESHOLD = 20.0  # Decrease slightly
```

### Problem: Recording doesn't stop after train passes

**Solutions:**
```python
FRAMES_NO_MOTION_TO_STOP = 45  # Decrease from 60
MOTION_THRESHOLD = 28.0  # Increase slightly
```

### Problem: Can't connect to DroidCam

**Solutions:**
1. Run `test_droidcam_connection.py` first
2. Check DroidCam app is running on phone
3. Verify IP address matches app display
4. Ensure phone and computer on same WiFi
5. Try accessing URL in web browser: `http://192.168.1.6:4747/video`
6. Disable firewall temporarily
7. Try USB connection instead: Set `DROIDCAM_URL = 0`

---

## Advanced: Using Local Webcam Instead

```python
# In motion_gate_droidcam.py or config file
DROIDCAM_URL = 0  # Use default webcam

# Or specific webcam
DROIDCAM_URL = 1  # Second webcam
```

---

## Performance

**Typical FPS:**
- Without saving: 25-30 FPS
- With saving: 20-25 FPS
- With MIMO deblurring: 2-5 FPS (depends on GPU)

**Memory Usage:**
- Base script: ~150 MB
- With background model: ~250 MB
- With MIMO model: ~2-4 GB (depends on model size)

---

## Comparison: Standalone vs Integrated System

### Standalone Script (This)

✅ Simple, easy to debug  
✅ No web server complexity  
✅ Direct control over parameters  
✅ Fast to test and iterate  
✅ Clear motion gate logic  

❌ No web interface  
❌ Manual operation only  

### Integrated Flask System

✅ Web dashboard UI  
✅ Remote access  
✅ Session management  
✅ Historical data  

❌ More complex  
❌ Harder to debug  
❌ More dependencies  

**Recommendation:** Start with standalone script to tune motion detection, then integrate into Flask system once working properly.

---

## Dependencies

```bash
pip install opencv-python numpy
```

That's it! No Flask, no PyTorch (unless you integrate MIMO), just pure OpenCV.

---

## Example Output

```
============================================================
MOTION GATE - Railway Wagon Inspection
============================================================
✓ Output folder: motion_gate_output/session_20251227_143055/frames
✓ Motion Threshold: 25.0%
✓ Min Contour Area: 8000 pixels
✓ Frames to Confirm: 15
✓ Frames to Stop: 60
============================================================

[CAMERA] Connecting to DroidCam: http://192.168.1.6:4747/video
[CAMERA] ✓ Connected successfully!

[MOTION GATE] Starting monitoring...
Press 'q' to quit, 'r' to reset background model

[MOTION GATE] Background learned. Now monitoring for motion...
[MOTION GATE] Motion detected! Confirming... (1/15)
[MOTION GATE] Confirming motion... (5/15) - 28.3%
[MOTION GATE] Confirming motion... (10/15) - 31.2%
[MOTION GATE] ✓✓✓ GATE OPENED ✓✓✓ Train confirmed! Capturing frames...
[MOTION GATE] No motion for 15/60 frames...
[MOTION GATE] No motion for 30/60 frames...
[MOTION GATE] No motion for 45/60 frames...
[MOTION GATE] ✗✗✗ GATE CLOSED ✗✗✗ Train passed. Returning to IDLE. (127 frames captured)
```

---

## License

MIT License - Free to use and modify

## Author

Railway Wagon Inspection System  
December 27, 2025
