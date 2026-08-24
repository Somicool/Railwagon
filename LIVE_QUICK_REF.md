# Live DroidCam Control - Quick Reference

## 🚀 Quick Start (3 Steps)

```powershell
# 1. Test DroidCam connection
python test_droidcam.py

# 2. If test passes, run processor
python live_simple_control.py

# 3. Start processing
Command: start

# 4. Stop processing
Press 'q' in video window
```

---

## 📋 Files Created

| File | Purpose |
|------|---------|
| `live_simple_control.py` | ⭐ **Main script** - Simple, recommended |
| `live_droidcam_processor.py` | Advanced version with threading |
| `test_droidcam.py` | Test camera connection |
| `LIVE_CONTROL_GUIDE.md` | Complete documentation |
| `LIVE_QUICK_REF.md` | This file |

---

## 🎮 Controls

### Starting
```
Type 'start' when prompted
```

### Stopping

**Simple version:**
- Press `q` in video window ✅

**Threaded version:**
- Press `q` in video window ✅
- Type `stop` in terminal ✅

---

## ⚙️ How It Works

### Start Logic
```python
# 1. Wait for user input
while True:
    cmd = input("Command: ")
    if cmd == 'start':
        break

# 2. Initialize processor
processor = SimpleLiveProcessor(...)

# 3. Open camera
cap = cv2.VideoCapture(0)

# 4. Start processing loop
processor.run()
```

### Stop Logic
```python
# In processing loop
while True:
    ret, frame = cap.read()
    # ... process frame ...
    
    # Check for 'q' key every frame
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break  # Exit loop

# Cleanup (ALWAYS runs)
cap.release()
cv2.destroyAllWindows()
```

---

## 🔧 Configuration

### Default Settings
```python
model_path = 'weights/gopro_best.pth'
output_dir = 'live_simple_output'
buffer_size = 3          # Frames to fuse
save_interval = 30       # Save every N frames
device = 'cuda'          # or 'cpu'
```

### Custom Settings
Edit `main()` function:
```python
processor = SimpleLiveProcessor(
    model_path='weights/gopro_best.pth',
    buffer_size=5,       # More smoothing
    save_interval=60,    # Less saving
    device='cpu'         # Use CPU
)
```

---

## 📁 Output Structure

```
live_simple_output/
├── 1_raw/
│   └── raw_00001_timestamp.jpg
├── 2_deblurred/
│   └── deblurred_00001_timestamp.jpg
└── 3_enhanced/
    └── enhanced_00001_timestamp.jpg
```

Saved every 30 frames (configurable)

---

## 🛡️ Safety Features

### Camera Always Released
```python
try:
    # Processing
    while True:
        ...
finally:
    # ALWAYS runs, even on error
    cap.release()
    cv2.destroyAllWindows()
```

### No Camera Lock
- Even if script crashes
- Even on Ctrl+C
- Even on exceptions

---

## 🐛 Troubleshooting

### Camera won't open
```powershell
# Test camera first
python test_droidcam.py

# Try different index
python test_droidcam.py 1
python test_droidcam.py 2
```

### Model not found
```powershell
# Check file exists
ls weights/gopro_best.pth

# If missing, update path or train model
```

### Too slow
```python
# Use GPU
device='cuda'

# Or reduce buffer
buffer_size=1

# Or save less
save_interval=100
```

### Out of memory
```python
# Use CPU instead
device='cpu'
```

---

## 📊 Processing Pipeline

```
DroidCam Frame
     ↓
[Deblurring] ← MIMO-UNet+
     ↓
[Frame Buffer] ← Store last N frames
     ↓
[Temporal Fusion] ← Median
     ↓
[Text Enhancement] ← CLAHE + Sharpen
     ↓
[Display + Save]
```

---

## 💡 Key Differences: Simple vs Threaded

| Feature | Simple | Threaded |
|---------|--------|----------|
| Code complexity | ⭐ Easy | ⭐⭐ Medium |
| Stop during processing | 'q' only | 'q' or 'stop' |
| Threading | No | Yes |
| Recommended for | Beginners | Advanced |

---

## 🎯 Demo Checklist

Before demo:
- [ ] DroidCam app running on phone
- [ ] DroidCam Client connected on PC
- [ ] Test camera: `python test_droidcam.py`
- [ ] Model weights exist: `weights/gopro_best.pth`
- [ ] Good lighting for phone camera

During demo:
- [ ] Run: `python live_simple_control.py`
- [ ] Type: `start`
- [ ] Show live video window
- [ ] Show saved results in output folder
- [ ] Press `q` to stop cleanly

---

## 📝 Example Session

```powershell
PS> python live_simple_control.py

============================================================
LIVE DROIDCAM PROCESSOR
============================================================

Type 'start' to begin live processing
============================================================

Command: start

Loading model from weights/gopro_best.pth...
✓ Model loaded on cuda
============================================================
SIMPLE LIVE PROCESSOR READY
============================================================
Device: cuda
Buffer: 3 frames
Save interval: Every 30 frames
Output: live_simple_output/
============================================================

============================================================
STARTING LIVE PROCESSING
============================================================

Opening DroidCam (camera 0)...
✓ Camera opened successfully

Press 'q' in video window to stop
============================================================
[Saved set 1 | Total frames: 30]
[Saved set 2 | Total frames: 60]
[Saved set 3 | Total frames: 90]

['q' pressed - stopping]

Cleaning up...

============================================================
LIVE PROCESSING STOPPED SUCCESSFULLY
============================================================
Total frames processed: 95
Frame sets saved: 3
Results saved in: live_simple_output
============================================================

Program ended.
```

---

## 🔗 Related Files

- Full guide: [LIVE_CONTROL_GUIDE.md](LIVE_CONTROL_GUIDE.md)
- Training: [GOPRO_TRAINING_GUIDE.md](GOPRO_TRAINING_GUIDE.md)
- Pipeline: [VIDEO_PIPELINE_README.md](VIDEO_PIPELINE_README.md)

---

## ✅ What You Accomplished

✅ **Terminal control** - Start only when you type 'start'  
✅ **Clean stop** - Press 'q' or type 'stop'  
✅ **No threading required** - Simple version uses basic Python  
✅ **Camera safety** - Always released, no lock issues  
✅ **Windows compatible** - Works on your system  
✅ **Demo ready** - Predictable, stable behavior  
✅ **Beginner friendly** - Clear code, easy to modify  

---

**Ready to go! Test with `python test_droidcam.py` first! 🚀**
