```
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║           LIVE DROIDCAM TERMINAL CONTROL                      ║
║           Simple Start/Stop for Video Pipeline               ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
```

## 🎯 What This Does

Live video processing from DroidCam with simple terminal control:

- **Type 'start'** → Begin processing
- **Press 'q'** → Stop processing
- **Automatic**: Deblur, fuse, enhance, save

---

## ⚡ 30-Second Start

```powershell
# 1. Test camera
python test_droidcam.py

# 2. Run processor
python live_simple_control.py

# 3. Start
Command: start

# 4. Stop
Press 'q' in window
```

---

## 📁 Files

| File | Purpose |
|------|---------|
| **test_droidcam.py** | Test camera connection |
| **live_simple_control.py** | ⭐ Main (recommended) |
| **live_droidcam_processor.py** | Advanced with threading |
| **LIVE_INDEX.md** | 📚 Start here for docs |
| **LIVE_QUICK_REF.md** | Quick reference |
| **LIVE_SUMMARY.md** | Complete overview |
| **LIVE_CONTROL_GUIDE.md** | Full documentation |
| **LIVE_CONTROL_DIAGRAM.md** | Visual diagrams |
| **LIVE_TROUBLESHOOTING.md** | Problem solving |

---

## 🎮 Controls

### Starting
```
Command: start
```

### Stopping

**Simple version:**
- Press `q` in video window

**Advanced version:**
- Press `q` in video window
- OR type `stop` in terminal

---

## 📊 Processing Pipeline

```
DroidCam → Deblur → Buffer → Fuse → Enhance → Display & Save
           ↓                                      ↓
        MIMO-UNet+                           Every 30 frames
```

---

## 📁 Output Structure

```
live_simple_output/
├── 1_raw/          ← Original frames
├── 2_deblurred/    ← After deblurring
└── 3_enhanced/     ← Final enhanced
```

---

## 🔧 Configuration

Edit `main()` in script:

```python
processor = SimpleLiveProcessor(
    model_path='weights/gopro_best.pth',
    buffer_size=3,      # Temporal fusion window
    save_interval=30,   # Save every N frames
    device='cuda'       # or 'cpu'
)
```

---

## 🐛 Troubleshooting

### Camera won't open
```powershell
python test_droidcam.py     # Test camera
python test_droidcam.py 1   # Try index 1
```

### Model not found
```powershell
ls weights/gopro_best.pth   # Check file exists
```

### Too slow
```python
device='cuda'        # Use GPU
buffer_size=1        # Disable fusion
```

**Full guide:** [LIVE_TROUBLESHOOTING.md](LIVE_TROUBLESHOOTING.md)

---

## 📚 Documentation

**New?** Start here: [LIVE_INDEX.md](LIVE_INDEX.md)

| Doc | When to Read |
|-----|--------------|
| [LIVE_INDEX.md](LIVE_INDEX.md) | Navigation guide |
| [LIVE_QUICK_REF.md](LIVE_QUICK_REF.md) | Quick lookup |
| [LIVE_SUMMARY.md](LIVE_SUMMARY.md) | Complete overview |
| [LIVE_CONTROL_GUIDE.md](LIVE_CONTROL_GUIDE.md) | Deep dive |
| [LIVE_CONTROL_DIAGRAM.md](LIVE_CONTROL_DIAGRAM.md) | Visual learner |
| [LIVE_TROUBLESHOOTING.md](LIVE_TROUBLESHOOTING.md) | Having issues |

---

## ✅ Requirements

- Python 3.8+
- PyTorch with CUDA (or CPU)
- OpenCV
- DroidCam app + client
- Model weights: `weights/gopro_best.pth`

---

## 🎯 Features

✅ **Terminal control** - Start only when you type 'start'  
✅ **Clean stop** - Press 'q' or type 'stop'  
✅ **Camera safety** - Always released, no lock issues  
✅ **Live preview** - See processing in real-time  
✅ **Auto-save** - Results saved periodically  
✅ **Pipeline processing** - Deblur → Fusion → Enhancement  
✅ **Windows compatible** - Works on your system  
✅ **Beginner friendly** - Clear code, easy to modify  

---

## 🎓 How It Works

### Start Control
```python
# Wait for 'start'
while True:
    cmd = input("Command: ")
    if cmd == 'start':
        break  # Then open camera and process
```

### Stop Control
```python
# In processing loop
while True:
    # ... process frames ...
    if cv2.waitKey(1) == ord('q'):
        break  # Exit loop

# Cleanup
cap.release()  # Camera always released
```

**Full explanation:** [LIVE_CONTROL_GUIDE.md](LIVE_CONTROL_GUIDE.md)

---

## 🚀 Next Steps

1. **Test camera:** `python test_droidcam.py`
2. **Run processor:** `python live_simple_control.py`
3. **Read docs:** [LIVE_INDEX.md](LIVE_INDEX.md)
4. **Customize:** Edit configuration
5. **Extend:** Add OCR, logging, etc.

---

## 🎬 Example Session

```powershell
PS> python live_simple_control.py

Type 'start' to begin live processing
Command: start

Loading model...
✓ Model loaded on cuda
Opening DroidCam (camera 0)...
✓ Camera opened successfully

Press 'q' in video window to stop
[Saved set 1 | Total frames: 30]
[Saved set 2 | Total frames: 60]
[Saved set 3 | Total frames: 90]

['q' pressed - stopping]

LIVE PROCESSING STOPPED SUCCESSFULLY
Total frames processed: 95
Results saved in: live_simple_output

Program ended.
```

---

## 💡 Pro Tips

**For demos:**
- Pre-open DroidCam before running
- Use simple version for stability
- Know where output saves

**For development:**
- Study both simple and threaded versions
- Read [LIVE_CONTROL_DIAGRAM.md](LIVE_CONTROL_DIAGRAM.md)
- Use GPU for speed

**For production:**
- Add error logging
- Implement reconnection logic
- Monitor performance

---

## 🔗 Related Guides

- Train model: [GOPRO_TRAINING_GUIDE.md](GOPRO_TRAINING_GUIDE.md)
- Batch processing: [VIDEO_PIPELINE_README.md](VIDEO_PIPELINE_README.md)
- Temporal fusion: [TEMPORAL_FUSION_GUIDE.md](TEMPORAL_FUSION_GUIDE.md)
- Add OCR: [OCR_IMPLEMENTATION_GUIDE.md](OCR_IMPLEMENTATION_GUIDE.md)

---

## 📞 Quick Help

**Camera issues?** → [LIVE_TROUBLESHOOTING.md#Camera](LIVE_TROUBLESHOOTING.md)  
**Too slow?** → [LIVE_TROUBLESHOOTING.md#Performance](LIVE_TROUBLESHOOTING.md)  
**Errors?** → [LIVE_TROUBLESHOOTING.md](LIVE_TROUBLESHOOTING.md)  
**How it works?** → [LIVE_CONTROL_GUIDE.md](LIVE_CONTROL_GUIDE.md)  

---

```
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║  Ready to start!                                              ║
║  Run: python test_droidcam.py                                 ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
```

---

*Created: 2025-12-23*  
*For: Live railway wagon inspection system*  
*By: GitHub Copilot*
