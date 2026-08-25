# Fix Green Screen Issue - Dashboard Live Streaming

## Problem
When clicking "START LIVE VIDEO" on the dashboard, only a green screen appears instead of the DroidCam video feed.

## Solution Applied

### 1. Fixed Camera Initialization
**File: `railway_dashboard/backend/inspection_processor.py`**

Changed camera backend from default to **DSHOW** (DirectShow) for better Windows compatibility:
```python
# OLD: cv2.VideoCapture(source)
# NEW: cv2.VideoCapture(source, cv2.CAP_DSHOW)
```

Added camera configuration for optimal streaming:
```python
self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimize latency
self.camera.set(cv2.CAP_PROP_FPS, 30)  # Request 30 FPS
```

### 2. Improved Frame Reading
**File: `railway_dashboard/backend/inspection_processor.py`**

Changed from `read()` to `grab()` + `retrieve()` for better performance:
```python
# OLD: ret, frame = self.camera.read()
# NEW: 
if self.camera.grab():
    ret, frame = self.camera.retrieve()
```

This reduces latency and prevents frame buffer buildup.

### 3. Enhanced Error Handling
**File: `railway_dashboard/backend/app.py`**

Added better debugging and error messages in the streaming endpoint:
- Track failed frame reads
- Log camera status
- Better diagnostic messages

### 4. Created Test Script
**File: `railway_dashboard/test_camera_stream.py`**

A diagnostic script to verify DroidCam works before testing the dashboard.

---

## How to Test the Fix

### Step 1: Test Camera Connection
```powershell
cd railway_dashboard
python test_camera_stream.py
```

**What to expect:**
- ✅ Camera should open successfully
- ✅ Should read 8-10 frames successfully
- ✅ Live window should show your phone camera feed
- Press 'q' to stop

### Step 2: Start the Backend Server
```powershell
cd railway_dashboard
.\start_server.ps1
```

**What to expect:**
- Server starts on http://localhost:5000
- No errors in console

### Step 3: Open Dashboard and Test
1. Open browser: http://localhost:5000
2. Login with your credentials
3. Click "LIVE VIDEO INSPECTION" in menu
4. Click "START LIVE VIDEO" button
5. **You should see your phone camera feed!** (not green screen)

---

## Troubleshooting

### Still seeing green screen?

**Check 1: Is DroidCam running?**
- ✅ DroidCam app running on phone
- ✅ DroidCam Client running on PC
- ✅ Connected (shows "Connected" status)

**Check 2: Is the camera index correct?**
Open `droidcam_config.py` and verify:
```python
DROIDCAM_URL = DROIDCAM_DEVICE  # Should be 1
```

If camera 1 doesn't work, try:
```python
DROIDCAM_URL = 2  # Or try 0, 2, 3
```

**Check 3: Check backend console logs**
Look for these messages:
```
[VIDEO SUCCESS] Live video started (Camera 1)
[VIDEO SUCCESS] Frame shape: (480, 640, 3)
[STREAM] First frame captured! Shape: (480, 640, 3)
```

If you see errors, they will indicate the problem.

**Check 4: Test direct camera access**
```powershell
python railway_dashboard/test_droidcam_connection.py
```

This will save a test frame. If it works, the issue is in the streaming.

### Common Issues

#### Issue: "Failed to open camera"
**Solution:** 
1. Restart DroidCam Client
2. Disconnect and reconnect phone
3. Try different camera index in `droidcam_config.py`

#### Issue: "Source opened but couldn't read frame"
**Solution:**
1. Close any other apps using the camera (Zoom, Teams, etc.)
2. Restart DroidCam Client
3. Check phone isn't in sleep mode

#### Issue: Browser shows "Video stream failed to load"
**Solution:**
1. Check backend console for errors
2. Try refreshing the page (Ctrl+R)
3. Clear browser cache
4. Try a different browser

---

## Technical Details

### Why DSHOW Backend?
- DirectShow is the native Windows camera API
- Better compatibility with virtual cameras like DroidCam
- More reliable than default backend on Windows

### Why grab() + retrieve()?
- `grab()` captures frame quickly without decoding
- `retrieve()` decodes only when needed
- Reduces latency in video streaming
- Prevents frame buffer overflow

### Camera Properties
- `BUFFERSIZE=1`: Keeps only latest frame (minimal latency)
- `FPS=30`: Requests 30 frames per second from camera

---

## Files Modified

1. **`railway_dashboard/backend/inspection_processor.py`**
   - Lines 203-231: Camera initialization with DSHOW backend
   - Lines 251-262: Frame reading with grab/retrieve

2. **`railway_dashboard/backend/app.py`**
   - Lines 130-189: Enhanced streaming endpoint

3. **`railway_dashboard/test_camera_stream.py`** (NEW)
   - Complete diagnostic test script

---

## Quick Reference

### Test sequence:
```powershell
# 1. Test camera
python railway_dashboard/test_camera_stream.py

# 2. Start server
cd railway_dashboard
.\start_server.ps1

# 3. Open browser
# http://localhost:5000

# 4. Click "START LIVE VIDEO"
# Should see camera feed!
```

### If problems persist:
1. Check DroidCam is connected
2. Run test_camera_stream.py
3. Check console logs for errors
4. Try different camera index in droidcam_config.py
5. Restart everything (DroidCam, backend server, browser)

---

## Success Indicators

✅ **test_camera_stream.py** shows live video
✅ **Backend logs** show "First frame captured"
✅ **Dashboard** displays camera feed (not green)
✅ **Console** shows "Streamed N frames" messages

If all above are ✅, the fix is working!

---

Last Updated: December 29, 2025
