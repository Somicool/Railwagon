# Live DroidCam Troubleshooting Guide

## Quick Diagnostic

Run these commands in order:

```powershell
# 1. Test DroidCam connection
python test_droidcam.py

# 2. If successful, run processor
python live_simple_control.py
```

---

## Common Issues & Solutions

### Issue 1: Camera Won't Open

**Error Message:**
```
ERROR: Could not open camera!
```

**Diagnostic Steps:**

1. **Check DroidCam App on Phone**
   ```
   ✓ DroidCam app is running
   ✓ Phone shows "Server Running"
   ✓ Shows IP address and port
   ```

2. **Check DroidCam Client on PC**
   ```
   ✓ DroidCam Client is open
   ✓ Connected to phone (USB or WiFi)
   ✓ Video preview is showing
   ```

3. **Test Camera Index**
   ```powershell
   # Try different camera indices
   python test_droidcam.py 0  # Default
   python test_droidcam.py 1  # If you have built-in webcam
   python test_droidcam.py 2
   ```

4. **Check if Camera is in Use**
   - Close other apps using camera (Zoom, Teams, etc.)
   - Close DroidCam preview in Client
   - Restart DroidCam Client

5. **Reconnect DroidCam**
   - Disconnect in DroidCam Client
   - Close DroidCam app on phone
   - Restart DroidCam app on phone
   - Reconnect in DroidCam Client

**Solution Code:**

If default camera index doesn't work, edit script:

```python
# In live_simple_control.py, change:
cap = cv2.VideoCapture(0)  # Original

# To:
cap = cv2.VideoCapture(1)  # Try 1, 2, 3...
```

---

### Issue 2: Model Weights Not Found

**Error Message:**
```
FileNotFoundError: weights/gopro_best.pth
```

**Diagnostic Steps:**

1. **Check if file exists:**
   ```powershell
   ls weights/gopro_best.pth
   ```

2. **Check current directory:**
   ```powershell
   pwd  # Should be in blur/ directory
   ```

3. **List weights directory:**
   ```powershell
   ls weights/
   ```

**Solutions:**

**Option 1: Update Path**

If weights file is named differently:
```python
# In main() function, change:
processor = SimpleLiveProcessor(
    model_path='weights/YOUR_ACTUAL_FILE.pth',  # Update this
    ...
)
```

**Option 2: Train Model**

If you don't have weights:
```powershell
# Train model first
python train.py
```

See [GOPRO_TRAINING_GUIDE.md](GOPRO_TRAINING_GUIDE.md) for details.

---

### Issue 3: CUDA Out of Memory

**Error Message:**
```
RuntimeError: CUDA out of memory
```

**Solutions:**

**Solution 1: Use CPU**
```python
# In main() function:
processor = SimpleLiveProcessor(
    device='cpu',  # Change from 'cuda' to 'cpu'
    ...
)
```

**Solution 2: Reduce Buffer Size**
```python
processor = SimpleLiveProcessor(
    buffer_size=1,  # Reduce from 3 to 1
    ...
)
```

**Solution 3: Close Other GPU Programs**
- Close other deep learning scripts
- Close games
- Close GPU-accelerated applications

**Solution 4: Lower Resolution**
- In DroidCam app settings, reduce video quality
- Or resize frames before processing:
  ```python
  # After cap.read()
  frame = cv2.resize(frame, (1280, 720))  # Lower resolution
  ```

---

### Issue 4: Processing Too Slow / Low FPS

**Symptoms:**
- Video window is choppy
- Long delay between frames
- Low FPS in output

**Diagnostic:**

Check what device is being used:
```
Device: cpu  ← Too slow!
Device: cuda ← Good!
```

**Solutions:**

**Solution 1: Use GPU**
```python
device='cuda'  # Make sure this is set
```

Verify CUDA is available:
```python
import torch
print(torch.cuda.is_available())  # Should be True
```

**Solution 2: Disable Temporal Fusion**
```python
buffer_size=1  # No fusion, faster
```

**Solution 3: Save Less Frequently**
```python
save_interval=100  # Save every 100 frames instead of 30
```

**Solution 4: Reduce Display Resolution**

Already done in script:
```python
display = cv2.resize(enhanced, (960, 540))  # Lower res
```

**Solution 5: Disable Video Display**

Comment out display code:
```python
# cv2.imshow('Live Processing', display)
# key = cv2.waitKey(1)
```

Then stop by typing 'stop' (threaded version only) or use Ctrl+C.

---

### Issue 5: Video Window Doesn't Show

**Symptoms:**
- Script runs but no window appears
- Can't press 'q' to stop

**Solutions:**

**Solution 1: Check Window Name**
```python
# Make sure you're looking for correct window
cv2.imshow('Live Processing', display)  # Window name
```

**Solution 2: Bring Window to Front**
- Alt+Tab to find window
- Click taskbar
- Window might be behind other windows

**Solution 3: Force Window to Front**

Add after `cv2.imshow()`:
```python
cv2.imshow('Live Processing', display)
cv2.setWindowProperty('Live Processing', cv2.WND_PROP_TOPMOST, 1)
```

**Solution 4: Check waitKey**

Make sure waitKey is called:
```python
key = cv2.waitKey(1)  # Must be called for window to update
```

---

### Issue 6: Can't Type 'stop' During Processing

**This is expected in simple version!**

The simple version (`live_simple_control.py`) only supports:
- Press `'q'` in video window

For terminal 'stop' command, use threaded version:
```powershell
python live_droidcam_processor.py
```

**Why?**

`input()` is blocking and pauses the processing loop. The threaded version runs `input()` in a separate thread.

---

### Issue 7: Camera Stays Locked After Crash

**Symptoms:**
- Previous run crashed
- New run fails with "Could not open camera"
- DroidCam Client shows camera in use

**Solutions:**

**Solution 1: Kill Python Processes**
```powershell
# Find Python processes
Get-Process python

# Kill all Python processes
Stop-Process -Name python -Force
```

**Solution 2: Restart DroidCam Client**
1. Close DroidCam Client
2. Close DroidCam app on phone
3. Wait 5 seconds
4. Start DroidCam app on phone
5. Start DroidCam Client on PC
6. Reconnect

**Solution 3: Disconnect/Reconnect Phone**
- Unplug USB cable
- Wait 5 seconds
- Plug back in
- Or disconnect WiFi and reconnect

**Prevention:**

The scripts use `try/finally` to prevent this:
```python
try:
    # Processing
finally:
    cap.release()  # Always releases camera
```

But if you force-kill (Task Manager), camera might stay locked.

---

### Issue 8: Import Errors

**Error Message:**
```
ModuleNotFoundError: No module named 'models'
```

**Solution:**

Make sure you're in the correct directory:
```powershell
cd C:\Users\Soham\OneDrive\Desktop\blur
python live_simple_control.py
```

**Error Message:**
```
ModuleNotFoundError: No module named 'cv2'
```

**Solution:**

Install OpenCV:
```powershell
pip install opencv-python
```

**Error Message:**
```
ModuleNotFoundError: No module named 'torch'
```

**Solution:**

Install PyTorch:
```powershell
pip install torch torchvision
```

---

### Issue 9: 'q' Key Doesn't Stop Processing

**Diagnostic:**

1. **Check Window is Active**
   - Click on video window
   - Window must have focus for key press to register

2. **Check waitKey is Called**
   ```python
   key = cv2.waitKey(1) & 0xFF  # Must be in loop
   if key == ord('q'):
       break
   ```

3. **Try Other Keys**
   - Press 'Q' (capital)
   - Press Escape key

**Solution:**

Make sure to:
1. Click video window to give it focus
2. Press lowercase 'q'
3. Window will close and script will cleanup

**Alternative Stop Methods:**

Threaded version:
```
Type: stop
```

Any version:
```
Press: Ctrl+C
```

---

### Issue 10: Saved Images are Black/Corrupt

**Diagnostic:**

Check if images are being saved:
```powershell
ls live_simple_output/1_raw/
```

Check image file size:
```powershell
ls -l live_simple_output/1_raw/raw_00001*.jpg
```

If size is very small (< 1 KB), images are corrupt.

**Solutions:**

**Solution 1: Check Frame is Valid**

Add debug print:
```python
ret, frame = cap.read()
if not ret:
    print("Failed to read frame!")
    continue

print(f"Frame shape: {frame.shape}")  # Should be (H, W, 3)
```

**Solution 2: Check Save Path**

Make sure directory exists:
```python
self.dirs['raw'].mkdir(parents=True, exist_ok=True)
```

**Solution 3: Verify Frame Type**

Before saving:
```python
print(f"Frame type: {type(frame)}")  # Should be numpy.ndarray
print(f"Frame dtype: {frame.dtype}")  # Should be uint8
```

---

### Issue 11: Threading Errors (Advanced Version)

**Error Message:**
```
RuntimeError: can't start new thread
```

**Solution:**

Use simple version instead:
```powershell
python live_simple_control.py
```

Or reduce number of threads in advanced version.

---

### Issue 12: Video Quality is Poor

**Symptoms:**
- Blurry output
- Low resolution
- Artifacts

**Solutions:**

**Solution 1: Improve DroidCam Quality**
- In DroidCam app settings, increase video quality
- Use USB connection instead of WiFi
- Improve lighting

**Solution 2: Increase Temporal Fusion**
```python
buffer_size=5  # More frames = smoother but slower
```

**Solution 3: Adjust CLAHE Parameters**
```python
clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
```

Lower clipLimit for less aggressive enhancement.

---

## Debug Mode

Add debug prints to diagnose issues:

```python
def run(self):
    print("[DEBUG] Opening camera...")
    cap = cv2.VideoCapture(0)
    print(f"[DEBUG] Camera opened: {cap.isOpened()}")
    
    while True:
        print("[DEBUG] Reading frame...")
        ret, frame = cap.read()
        print(f"[DEBUG] Frame read: {ret}, shape: {frame.shape if ret else 'None'}")
        
        print("[DEBUG] Deblurring...")
        deblurred = self._deblur_frame(frame)
        print(f"[DEBUG] Deblurred shape: {deblurred.shape}")
        
        # ... rest of processing ...
        
        if cv2.waitKey(1) == ord('q'):
            print("[DEBUG] 'q' pressed, breaking loop")
            break
    
    print("[DEBUG] Cleanup...")
    cap.release()
    cv2.destroyAllWindows()
    print("[DEBUG] Done")
```

---

## System Requirements Check

**Minimum Requirements:**
- Python 3.8+
- 8 GB RAM (CPU mode)
- 4 GB GPU RAM (GPU mode)
- Windows 10+

**Check Python Version:**
```powershell
python --version  # Should be 3.8 or higher
```

**Check PyTorch:**
```powershell
python -c "import torch; print(torch.__version__)"
```

**Check CUDA:**
```powershell
python -c "import torch; print(torch.cuda.is_available())"
```

**Check OpenCV:**
```powershell
python -c "import cv2; print(cv2.__version__)"
```

---

## Getting Help

If issues persist:

1. **Check full error traceback**
   - Read entire error message
   - Note line number where error occurs

2. **Run test script first**
   ```powershell
   python test_droidcam.py
   ```

3. **Test with minimal code**
   - Comment out processing
   - Just test camera open/close

4. **Check related guides**
   - [LIVE_CONTROL_GUIDE.md](LIVE_CONTROL_GUIDE.md) - Full documentation
   - [LIVE_QUICK_REF.md](LIVE_QUICK_REF.md) - Quick reference
   - [LIVE_CONTROL_DIAGRAM.md](LIVE_CONTROL_DIAGRAM.md) - Visual guide

---

## Error Reporting Template

If you need to report an issue, include:

```
**System:**
- OS: Windows 11
- Python version: 3.9.7
- PyTorch version: 2.0.1
- CUDA available: Yes/No

**DroidCam:**
- Connection type: USB/WiFi
- Camera index: 0
- DroidCam Client version: X.X.X

**Error:**
[Paste full error traceback here]

**What I tried:**
1. Step 1
2. Step 2
3. ...

**Result:**
Still not working / Partial success / etc.
```

---

**Most issues can be solved by restarting DroidCam and checking camera index!**
