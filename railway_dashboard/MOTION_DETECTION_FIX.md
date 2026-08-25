# Motion Detection Fix - Auto Mode Enabled by Default

## Problem
When pressing "START INSPECTION", the system was deblurring and processing ALL frames immediately, instead of waiting for train detection via motion detection.

## Root Cause
**Auto Mode (Motion Detection) was OFF by default**, which meant the system ran in MANUAL mode and captured every single frame.

In the code:
- **Manual Mode** (`autoMode: false`): Process ALL frames immediately
- **Auto Mode** (`autoMode: true`): Only process frames AFTER train is detected via motion detection

## Solution Applied

### Changed Auto Mode to ON by default:

**File: `railway_dashboard/script.js`** (Line 20)
```javascript
// BEFORE:
autoMode: false,

// AFTER:
autoMode: true,  // Changed to ON by default - only process when train detected
```

**File: `railway_dashboard/index.html`** (Lines 154-156)
```html
<!-- BEFORE: -->
<input type="checkbox" id="autoModeToggle">
<span id="autoModeLabel" class="toggle-label">OFF</span>

<!-- AFTER: -->
<input type="checkbox" id="autoModeToggle" checked>
<span id="autoModeLabel" class="toggle-label">ON</span>
```

---

## How Motion Detection Works Now

### State Machine Flow:

1. **LEARNING (60 frames)**: System learns background for ~2 seconds
   - No frame capture
   - Building background model

2. **IDLE**: Waiting for motion
   - Continuously scanning for movement
   - No frame capture yet

3. **MOTION_CANDIDATE**: Motion detected
   - Validates if motion is significant
   - Still no frame capture

4. **TRAIN_CONFIRMED**: Validated as a train
   - Motion is large enough (>12% width, >6% height)
   - Wide aspect ratio (width/height > 1.8)
   - Sustained for 7 consecutive frames
   - **✅ FRAME CAPTURE BEGINS**

5. **INSPECTION_RUNNING**: Processing frames
   - Deblurring active frames
   - Running OCR on wagon numbers
   - Saving results

6. **AUTO-STOP**: Train passes
   - No motion for 60 frames (~2 seconds)
   - **❌ FRAME CAPTURE STOPS**
   - Returns to IDLE state

---

## Testing the Fix

### Before Fix:
1. Click "START INSPECTION"
2. ❌ System immediately starts deblurring ALL frames
3. ❌ Processes background, walls, empty tracks

### After Fix:
1. Click "START INSPECTION"
2. ✅ System waits in IDLE state
3. ✅ Only starts processing when train enters frame
4. ✅ Auto-stops when train exits

---

## User Interface

The **MOTION DETECTION AUTO MODE** panel shows:
- **Toggle**: ON/OFF switch (now ON by default)
- **State Display**: IDLE → MOTION_CANDIDATE → INSPECTION_RUNNING
- **Motion Level**: Current motion percentage (0-100%)
- **Train Confirmed**: Shows if train is detected

**You can still toggle it OFF** if you want manual mode (process all frames).

---

## Train Detection Rules (Configured)

From `inspection_processor.py`:
```python
train_min_width_ratio = 0.12      # Train must be >12% of frame width
train_min_height_ratio = 0.06     # Train must be >6% of frame height  
train_aspect_ratio_min = 1.8      # Width/Height must be >1.8 (wide object)
train_confirmation_frames = 7     # Must persist for 7 frames
no_motion_frames_to_stop = 60    # Auto-stop after 60 frames without motion
```

These are already optimized for train detection and should work well.

---

## Console Messages

When Auto Mode is working correctly, you'll see:

```
[STATE MACHINE] Starting in IDLE state
[MOTION] Learning background for 60 frames...
[STATE MACHINE] Learning complete. Entering IDLE state.
[IDLE] Frame 70: motion_pct=1.23%, has_motion=False, threshold=5.0%
[STATE MACHINE] IDLE → MOTION_CANDIDATE (motion=12.5%)
[TRAIN VALIDATION] Confirming... (1/7) - ...
[STATE MACHINE] ✓✓✓ MOTION_CANDIDATE → INSPECTION_RUNNING ✓✓✓
[TRAIN CONFIRMED] Train detected: Width=15.2%, Height=8.5%, Aspect=2.1
[INSPECTION] Frame capture ENABLED
[Saved deblurred_000001.jpg]
[Saved deblurred_000002.jpg]
...
[STATE MACHINE] ✗✗✗ INSPECTION_RUNNING → IDLE ✗✗✗ (train passed)
[INSPECTION] Frame capture DISABLED
```

---

## Manual Mode Override

If you need to process ALL frames (testing, etc.):
1. Toggle **MOTION DETECTION AUTO MODE** to **OFF**
2. Click "START INSPECTION"
3. System will capture every frame immediately

---

## Quick Reference

| Mode | When Processing Starts | Use Case |
|------|----------------------|----------|
| **Auto Mode (ON)** | Only when train detected | ✅ Normal operation |
| **Manual Mode (OFF)** | Immediately | Testing/debugging only |

**Default: Auto Mode ON** - Saves processing power and storage!

---

Last Updated: December 29, 2025
