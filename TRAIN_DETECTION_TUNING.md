# Train Detection Tuning Guide

## Current Settings (RELAXED for Better Detection)

### Stage 1: Motion Candidate Detection
```python
motion_threshold = 20.0%         # Down from 35% - more sensitive
min_contour_area = 8000 pixels   # Down from 15000 - detects smaller objects
motion_frames_to_candidate = 5   # 5 consecutive frames with motion
```

### Stage 2: Train Confirmation
```python
train_confirmation_frames = 7        # Down from 10 - faster confirmation
train_min_width_ratio = 0.12 (12%)   # Down from 20% - allows narrower trains
train_min_height_ratio = 0.06 (6%)   # Down from 10% - allows shorter trains
train_aspect_ratio_min = 1.8         # Down from 2.5 - allows less-wide objects
```

---

## What Changed

| Parameter | OLD (Too Strict) | NEW (Relaxed) | Effect |
|-----------|------------------|---------------|--------|
| Motion Threshold | 35% | 20% | Detects motion earlier |
| Min Contour Area | 15000px | 8000px | Detects smaller/distant trains |
| Width Requirement | 20% | 12% | Allows trains farther from camera |
| Height Requirement | 10% | 6% | Allows trains at different angles |
| Aspect Ratio | 2.5 | 1.8 | Less strict on shape (allows wagons) |
| Confirmation Frames | 10 | 7 | Faster train confirmation |

---

## Expected Behavior

### ✅ NOW DETECTS (Previously Rejected)
- Trains farther from camera (smaller in frame)
- Individual wagons (may not be as wide)
- Trains at slight angles
- Slower-moving trains
- Trains with gaps between wagons

### ⚠️ MAY STILL DETECT (Potential False Positives)
- Large vehicles (trucks, buses) if they occupy >12% width
- People walking close to camera
- Large animals
- Moving equipment

### ❌ SHOULD STILL REJECT
- Static walls/backgrounds
- Small people in distance
- Cars (too small)
- Lighting changes
- Camera shake

---

## Further Tuning

### If STILL rejecting trains:
```python
# Make even MORE lenient
motion_threshold = 15.0              # Even more sensitive
min_contour_area = 5000              # Detect very small trains
train_min_width_ratio = 0.10         # Allow 10% width
train_min_height_ratio = 0.05        # Allow 5% height
train_aspect_ratio_min = 1.5         # Even less strict on shape
train_confirmation_frames = 5        # Confirm in just 5 frames
```

### If getting TOO MANY false positives:
```python
# Make more strict (but not as strict as before)
motion_threshold = 25.0              # Less sensitive
min_contour_area = 10000             # Larger objects only
train_min_width_ratio = 0.15         # Require 15% width
train_min_height_ratio = 0.08        # Require 8% height
train_aspect_ratio_min = 2.0         # More strict on shape
train_confirmation_frames = 10       # Need 10 frames to confirm
```

---

## How to Test

1. **Refresh dashboard** (F5)
2. **Enable AUTO MODE** (toggle ON)
3. **Wait for LEARNING** (60 frames)
4. **Point camera at train**
5. **Watch terminal output:**

```
[TRAIN RULES] Width>12%, Height>6%, Aspect>1.8, Frames=7
[STATE MACHINE] IDLE → MOTION_CANDIDATE (motion=22.3%)
[TRAIN VALIDATION] Confirming... (1/7) - TRAIN CONFIRMED (size=14.2%x7.5%, aspect=1.9)
[TRAIN VALIDATION] Confirming... (2/7) - TRAIN CONFIRMED (size=15.1%x8.2%, aspect=1.8)
...
[STATE MACHINE] ✓✓✓ MOTION_CANDIDATE → TRAIN_CONFIRMED ✓✓✓
```

---

## Rejection Reasons

If train is still rejected, terminal will show WHY:

```
[TRAIN VALIDATION] REJECTED: Width too small (11.5% < 12%)
[TRAIN VALIDATION] REJECTED: Height too small (5.2% < 6%)
[TRAIN VALIDATION] REJECTED: Not wide enough (aspect=1.6 < 1.8)
[TRAIN VALIDATION] REJECTED: No horizontal motion detected
```

Use these messages to determine which parameter to adjust.

---

## Quick Parameter Location

File: `railway_dashboard/backend/inspection_processor.py`

Lines ~40-50:
```python
self.motion_threshold = 20.0
self.min_contour_area = 8000

self.train_confirmation_frames = 7
self.train_min_width_ratio = 0.12
self.train_min_height_ratio = 0.06
self.train_aspect_ratio_min = 1.8
```

Save file → Flask auto-reloads → Test again

---

## Recommended Approach

1. **Test with current RELAXED settings**
2. **Check terminal for rejection reasons**
3. **Adjust ONE parameter at a time**
4. **Test again**
5. **Repeat until trains detected reliably**

**Goal:** Find the sweet spot where trains pass but walls/people fail.

---

## System Status

✅ State machine working correctly
✅ Two-stage validation implemented
✅ Dashboard UI updated
✅ Auto-stop working
⚙️ **TUNING PHASE** - Adjust thresholds to match your specific use case

The system is functioning correctly - it just needs threshold tuning for your specific camera angle, distance, and train size! 🚂
