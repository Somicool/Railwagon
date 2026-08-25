# Live Damage Detection Guide

## ✅ Integration Complete

Damage detection from recorded video pipeline has been successfully integrated into live video processing!

## 🔧 What Changed

### 1. **Both Live Processors Updated**
- ✅ `live_droidcam_processor.py` - Multi-threaded live processor
- ✅ `live_simple_control.py` - Simple single-threaded processor

### 2. **Features Added**
- ✅ **WagonDamageDetector** imported and initialized
- ✅ **Damage detection** runs on every deblurred frame
- ✅ **Train detection** prevents false positives from background
- ✅ **Annotated images** saved with damage markings
- ✅ **Damage tracking** with statistics and summaries
- ✅ **Lower threshold** for live video (10% vs 15%)

### 3. **Output Structure**
```
live_output/                      or    live_simple_output/
├── 1_raw_frames/                      ├── deblurred_frames/
├── 2_deblurred/                       └── damage_detections/
├── 3_enhanced/                            ├── damage_00001.jpg
├── 4_ocr_results/                         ├── damage_00045.jpg
└── 5_damage_detections/  ← NEW!           └── ...
    ├── damage_00001.jpg
    ├── damage_00045.jpg
    └── ...
```

---

## 🚀 How to Use

### Run Live Damage Detection

```bash
# Option 1: Full-featured processor
python live_droidcam_processor.py

# Option 2: Simple processor
python live_simple_control.py
```

### What to Expect

**On Startup:**
```
[DEBUG] Looking for damage_detector at: C:\...\railway_dashboard\backend
[DEBUG] Path exists: True
[DEBUG] WagonDamageDetector imported successfully

[DAMAGE DETECTION] DAMAGE_DETECTION_AVAILABLE = True
[DAMAGE DETECTION] Loading Wagon Damage Detector...
Wagon Damage Detector initialized (Device: cuda, Min Coverage: 10.0%)
[DAMAGE DETECTION] ✓ Damage Detector loaded successfully
[DAMAGE DETECTION]   - Min train coverage: 10% (optimized for live video)

Device: cuda
Damage Detection: ENABLED  ✓
```

**During Processing (when train visible):**
```
Frame 45... 
[DAMAGE DETECTOR] Train detected (23.5% coverage) - proceeding with damage detection
[DAMAGE DETECTOR] No window/door regions found - skipping damage detection

Frame 67...
[DAMAGE DETECTOR] Train detected (28.2% coverage) - proceeding with damage detection
⚠⚠⚠ DAMAGE DETECTED: crack (Confidence: 75.3%, Train: 28.2%)
[Saved 3 sets | Total frames: 90 | Damages: 1]
```

**During Processing (when no train):**
```
Frame 12...
[DAMAGE DETECTOR] No significant train detected (3.2% < 10.0%) - skipping damage detection
```

**Final Summary:**
```
============================================================
PROCESSING COMPLETE
============================================================
Total frames processed: 450
Total frames saved: 450
Damage detections: 8
  Types detected:
    - crack: 5
    - broken_glass: 2
    - structural: 1
Output location: live_simple_output
============================================================
```

---

## 🔍 How Damage Detection Works

### 1. **Train Detection First** (Prevents False Positives)
- Analyzes frame for train presence
- Checks edge density, horizontal lines, connected components
- **Requires ≥10% train coverage** (reduced from 15% for live video)
- If no train → skip damage detection (avoids background false positives)

### 2. **Window/Door Detection**
- Identifies rectangular regions (windows/doors)
- Uses contour detection and aspect ratio analysis
- Only analyzes these regions for damage

### 3. **Multi-Method Damage Detection**

#### **Method 1: Crack Detection**
- Edge detection using Canny
- Morphological operations to connect crack segments
- Filters out short/isolated edges

#### **Method 2: Broken Glass Detection**
- Texture analysis using Local Binary Patterns
- Detects irregular glass patterns
- Identifies shattered/spider-web patterns

#### **Method 3: Structural Damage**
- Contour irregularity analysis
- Detects deformed/bent frames
- Identifies missing sections

### 4. **Damage Annotation**
- **Red boxes** = Cracks
- **Orange boxes** = Broken glass  
- **Yellow boxes** = Structural damage
- Confidence scores displayed on each detection

---

## 🐛 Troubleshooting

### Issue: "Damage Detection: DISABLED"

**Cause:** Import failed

**Fix:**
```bash
# Test import manually
python test_damage_import.py

# Should show:
# ✓ WagonDamageDetector imported successfully
# ✓ Damage detector initialized successfully
```

### Issue: "No significant train detected"

**Cause:** Train not visible enough (< 10% of frame)

**Solutions:**
1. **Point camera at train** - Make sure train is in view
2. **Zoom in** - Train should occupy significant portion of frame
3. **Adjust threshold** - Lower `min_train_coverage` to 0.05 (5%):

```python
# In live_droidcam_processor.py or live_simple_control.py
self.damage_detector = WagonDamageDetector(
    device=device,
    min_train_coverage=0.05  # Lower to 5% for distant trains
)
```

### Issue: "No window/door regions found"

**Cause:** No rectangular regions detected (windows/doors)

**Solutions:**
1. **Wait for train** - Let a wagon with windows pass by
2. **Better lighting** - Ensure good visibility
3. **Clean camera** - Remove obstructions

### Issue: Too Many False Positives

**Cause:** Threshold too sensitive

**Fix:** Increase train coverage requirement:
```python
self.damage_detector = WagonDamageDetector(
    device=device,
    min_train_coverage=0.20  # Increase to 20% for stricter detection
)
```

---

## 📊 Understanding Output

### Damage Detection Image
Each saved damage image shows:
- **Bounding boxes** around detected damage
- **Labels** with damage type
- **Confidence scores** (0-100%)
- **Original frame** with annotations

### Damage Tracking
Each damage detection records:
```python
{
    'frame': 145,                    # Frame number
    'damage_type': 'crack',          # Primary type
    'damage_types': ['crack'],       # All types detected
    'confidence': 0.753,             # Average confidence
    'damage_count': 2                # Number of damage regions
}
```

---

## 🎯 Best Practices

### 1. **Camera Setup**
- Point directly at passing trains
- Train should occupy 15-30% of frame
- Good lighting conditions
- Stable mounting (reduce camera shake)

### 2. **Performance Optimization**
- Use **GPU** (CUDA) for faster processing
- Adjust `save_interval` to reduce disk writes
- Lower resolution if needed (but keep details visible)

### 3. **Damage Detection Accuracy**
- **Best:** Clear, well-lit wagon windows/doors
- **Good:** Slightly blurry but train visible
- **Poor:** Heavy blur, low light, no train visible

### 4. **Reviewing Results**
- Check `damage_detections/` folder for annotated images
- Review damage statistics in final summary
- Verify detections against original frames

---

## 🔬 Testing Damage Detection

### Test with Recorded Video
```bash
# Use your existing railway video
python live_simple_control.py
# Point to video file when prompted, or modify to use file instead of camera
```

### Test with Sample Images
```bash
# Test on single image
cd railway_dashboard/backend
python damage_detector.py path/to/wagon_image.jpg
```

### Expected Results
- ✅ Cracks on windows → **Red boxes**
- ✅ Broken glass → **Orange boxes**
- ✅ Bent frames → **Yellow boxes**
- ✅ No train → **No detection** (correct!)
- ✅ Background objects → **No detection** (correct!)

---

## 📝 Summary

### ✅ What Works
- Import and initialization of damage detector
- Train presence detection (prevents false positives)
- Window/door region detection
- Multi-method damage detection (cracks, glass, structural)
- Annotated image saving
- Statistics and tracking
- Lower threshold for live video (10% vs 15%)

### ⚠️ Requirements for Detection
1. **Train must be visible** (≥10% of frame)
2. **Windows/doors must be detectable** (rectangular regions)
3. **Reasonable image quality** (not too blurry/dark)

### 🎯 Key Difference from Recorded Video
- **Live:** 10% min train coverage (more lenient)
- **Recorded:** 15% min train coverage (stricter)
- **Reason:** Live video may have partial/edge-of-frame trains

---

## 🆘 Support

If damage detection still not working:

1. **Run test script:**
   ```bash
   python test_damage_import.py
   ```

2. **Check debug output** when running live processor:
   - Look for `[DAMAGE DETECTION]` messages
   - Check if `DAMAGE_DETECTION_AVAILABLE = True`
   - Verify `Damage Detection: ENABLED`

3. **Review train detection:**
   - Messages show train coverage percentage
   - Needs ≥10% to proceed with damage detection

4. **Verify train is in frame:**
   - During live processing, watch the video window
   - Ensure train wagons are visible and occupy significant portion

---

**Last Updated:** January 5, 2026  
**Status:** ✅ Fully Integrated and Tested
