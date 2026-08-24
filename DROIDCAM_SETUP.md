# DroidCam Setup Guide - Quick Start

## 🎯 Problem Solved

Your scripts will now:
- ✅ **NEVER** use laptop webcam automatically
- ✅ **ALWAYS** try DroidCam IP stream first
- ✅ **FALLBACK** to camera indices 1, 2, 3 (skipping 0)
- ✅ **FAIL CLEARLY** if DroidCam not found

---

## 🚀 Setup (3 Steps)

### Step 1: Find Your Phone's IP

1. Open **DroidCam app** on your phone
2. Look for this on the screen:
   ```
   WiFi IP: 192.168.X.XXX
   ```
3. **Copy that IP address**

### Step 2: Update Configuration

1. Open `droidcam_config.py`
2. Find this line:
   ```python
   DROIDCAM_IP = "192.168.1.100"  # ← CHANGE THIS!
   ```
3. Change to your phone's IP:
   ```python
   DROIDCAM_IP = "192.168.0.105"  # Example
   ```
4. **Save the file**

### Step 3: Test Connection

```powershell
python test_droidcam.py
```

This will:
- Test IP stream connection
- List all available cameras
- Identify which is DroidCam
- Give you clear instructions

---

## 📋 How It Works Now

### Connection Priority

```
1. TRY: DroidCam IP Stream
   http://YOUR_PHONE_IP:4747/video
   ↓
   SUCCESS? → Use this ✓
   FAIL? → Continue
   
2. TRY: Camera Index 1
   cv2.VideoCapture(1)
   ↓
   Available & high-res? → Use this ✓
   FAIL? → Continue
   
3. TRY: Camera Index 2
   cv2.VideoCapture(2)
   ↓
   Available & high-res? → Use this ✓
   FAIL? → Continue
   
4. TRY: Camera Index 3
   cv2.VideoCapture(3)
   ↓
   Available & high-res? → Use this ✓
   FAIL? → Error message

NOTE: Camera Index 0 (laptop webcam) is NEVER tried!
```

---

## 🔍 Testing Methods

### Method 1: Comprehensive Test (Recommended)

```powershell
python test_droidcam.py
```

**What it does:**
- Tests IP stream
- Scans all camera indices
- Shows live preview of each camera
- Tells you which is DroidCam

**Example output:**
```
[TEST 1] DroidCam IP Stream
  URL: http://192.168.1.100:4747/video
  ✓ SUCCESS! DroidCam IP stream working

[TEST 2] Scanning Camera Indices (0-5)

Camera index 0:
  ✓ Available
  Resolution: 640x480
  Type: Likely LAPTOP WEBCAM

Camera index 1:
  ✓ Available
  Resolution: 1920x1080
  Type: Likely PHONE (DroidCam)
  ⭐ RECOMMENDED: Use this for DroidCam
```

### Method 2: Test Specific Camera

```powershell
python test_droidcam.py --index 1
```

### Method 3: Test Custom IP

```powershell
python test_droidcam.py --ip 192.168.0.105
```

---

## ✅ Verification

### How to Verify Correct Camera

When you run `python live_simple_control.py`:

```
Command: start

Searching for DroidCam...

[Method 1] Trying DroidCam IP stream...
  URL: http://192.168.1.100:4747/video
  ✓ Connected! (1920x1080)

============================================================
✓ CONNECTED TO: DroidCam IP stream (http://192.168.1.100:4747/video)
============================================================
```

**Good signs:**
- ✅ Says "DroidCam IP stream" or "Camera index 1/2"
- ✅ Resolution is 1280x720 or higher
- ✅ NOT camera index 0

**Bad signs:**
- ❌ "Camera index 0" (that's your laptop!)
- ❌ Low resolution (640x480)
- ❌ "ERROR: DroidCam NOT FOUND"

---

## 🔧 Configuration Options

### Edit `droidcam_config.py`

```python
# Your phone's IP (REQUIRED)
DROIDCAM_IP = "192.168.1.100"  # ← Change this

# Port (usually 4747, don't change)
DROIDCAM_PORT = 4747

# Which camera indices to try (in order)
CAMERA_INDICES_TO_TRY = [1, 2, 3]  # Skips 0 = laptop

# Minimum resolution to accept as DroidCam
MIN_DROIDCAM_WIDTH = 640
MIN_DROIDCAM_HEIGHT = 480
```

---

## 📱 DroidCam Connection Methods

### Method A: IP Stream (Recommended)

**Pros:**
- Most reliable
- Works over WiFi
- No DroidCam Client needed

**Setup:**
1. Connect phone and PC to same WiFi
2. Open DroidCam app on phone
3. Note the IP shown
4. Update `droidcam_config.py`

**How to use:**
```python
from droidcam_config import DROIDCAM_URL
cap = cv2.VideoCapture(DROIDCAM_URL)
```

### Method B: Virtual Camera (via DroidCam Client)

**Pros:**
- Works with any app
- No IP configuration needed

**Setup:**
1. Install DroidCam Client on PC
2. Connect phone (USB or WiFi)
3. DroidCam Client creates virtual camera
4. Usually appears as camera index 1

**How to use:**
```python
cap = cv2.VideoCapture(1)  # or 2, 3
```

---

## 🐛 Troubleshooting

### Issue: "ERROR: DroidCam NOT FOUND"

**Solution 1: Check Phone IP**
```powershell
# Test with your phone's actual IP
python test_droidcam.py --ip YOUR_PHONE_IP
```

**Solution 2: Use DroidCam Client**
1. Open DroidCam Client on PC
2. Connect to phone
3. Run: `python test_droidcam.py`
4. It will find the virtual camera

**Solution 3: Manual Camera Selection**

Edit scripts to force a specific index:
```python
# In live_simple_control.py
cap = cv2.VideoCapture(1)  # Force index 1
```

### Issue: Still Using Laptop Webcam

**Verify by checking output:**
```
✓ CONNECTED TO: Camera index 0 (640x480)  ← BAD! This is laptop
```

**Solution:**
The new code **never tries index 0** unless you force it. If you see this, the script wasn't updated correctly.

**Quick fix:**
```powershell
# Re-download or check the script
python test_droidcam.py
```

### Issue: Can't Connect to IP Stream

**Checklist:**
- [ ] Phone and PC on **same WiFi**
- [ ] DroidCam app **running** on phone
- [ ] **Correct IP** in `droidcam_config.py`
- [ ] Firewall **not blocking**
- [ ] VPN **disabled**

**Test manually:**
```powershell
# Test in browser first
# Open: http://YOUR_PHONE_IP:4747/video
# Should show video stream
```

---

## 📊 Comparison: Before vs After

### BEFORE (Old Code)

```python
cap = cv2.VideoCapture(0)  # Always tries laptop webcam!
```

**Problems:**
- ❌ Uses laptop webcam by default
- ❌ No DroidCam detection
- ❌ Manual camera selection needed

### AFTER (New Code)

```python
cap, source = self._find_droidcam()
# Tries:
#   1. IP stream: http://192.168.1.100:4747/video
#   2. Camera 1, 2, 3 (skips 0)
```

**Benefits:**
- ✅ Never uses laptop webcam automatically
- ✅ Smart DroidCam detection
- ✅ Clear error messages
- ✅ Easy IP configuration

---

## 🎓 Technical Details

### Smart Detection Logic

```python
def _find_droidcam(self):
    # Try IP stream first
    cap = cv2.VideoCapture(DROIDCAM_URL)
    if cap.isOpened() and can_read_frame():
        return cap, "DroidCam IP stream"
    
    # Try camera indices (skip 0)
    for index in [1, 2, 3]:
        cap = cv2.VideoCapture(index)
        if cap.isOpened() and resolution_is_good():
            return cap, f"Camera index {index}"
    
    # Not found
    return None, None
```

### Resolution Filtering

```python
# Only accept cameras with decent resolution
if width >= 640 and height >= 480:
    return cap  # Probably DroidCam
else:
    skip  # Probably low-quality webcam
```

---

## 📁 Files Modified

| File | Changes |
|------|---------|
| `live_simple_control.py` | Added `_find_droidcam()` method |
| `live_droidcam_processor.py` | Added `_find_droidcam()` method |
| `test_droidcam.py` | Comprehensive testing tool |
| `droidcam_config.py` | ⭐ **NEW** - Centralized config |
| `DROIDCAM_SETUP.md` | This file |

---

## ✅ Quick Checklist

Setup:
- [ ] Find phone IP in DroidCam app
- [ ] Update `droidcam_config.py`
- [ ] Run `python test_droidcam.py`

Verification:
- [ ] IP stream test passes **OR**
- [ ] Camera index 1/2 identified as DroidCam
- [ ] Script says "DroidCam IP stream" or "Camera index 1/2"
- [ ] NOT saying "Camera index 0"

Ready to use:
- [ ] Run `python live_simple_control.py`
- [ ] Type: `start`
- [ ] Verify correct camera in output
- [ ] Check video quality in preview

---

## 🎯 Summary

**What changed:**
1. Scripts **never** use camera index 0 (laptop webcam)
2. IP stream tried **first** (most reliable)
3. Camera indices 1, 2, 3 tried as **fallback**
4. Clear **error messages** if DroidCam not found
5. Centralized **configuration** in one file

**What you need to do:**
1. Update phone IP in `droidcam_config.py`
2. Run `python test_droidcam.py`
3. Verify it finds DroidCam
4. Use normally!

---

**You're all set! Test now with: `python test_droidcam.py`** 🚀
