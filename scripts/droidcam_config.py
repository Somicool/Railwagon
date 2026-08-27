"""
DroidCam Configuration
======================

Centralized configuration for DroidCam connection.

HOW TO FIND YOUR PHONE'S IP:
1. Open DroidCam app on your phone
2. Look at the screen - it shows: "WiFi IP: XXX.XXX.XXX.XXX"
3. Copy that IP address and paste it below
4. Save this file

Example: If DroidCam shows "WiFi IP: 192.168.0.105"
         Then set: DROIDCAM_IP = "192.168.0.105"
"""

# ============================================================
# DROIDCAM IP CONFIGURATION
# ============================================================

# CHANGE THIS to your phone's IP address (shown in DroidCam app)
DROIDCAM_IP = "192.168.1.10"  # ← Your phone's IP from DroidCam app

# DroidCam default port (usually 4747, don't change unless needed)
DROIDCAM_PORT = 4747

# DroidCam Virtual Webcam Device (when using DroidCam PC client)
DROIDCAM_DEVICE = 0  # DroidCam Client device index

# Video stream URL (constructed automatically)
# OPTION 1: Use device index (virtual webcam) - REQUIRES DroidCam PC Client running
DROIDCAM_URL = DROIDCAM_DEVICE  # Using Camera 0 (DroidCam Client virtual camera)
# OPTION 2: Use WiFi IP stream - Direct connection to phone
# DROIDCAM_URL = f"http://{DROIDCAM_IP}:{DROIDCAM_PORT}/video"  # WiFi direct mode

# ============================================================
# CAMERA INDEX FALLBACK
# ============================================================

# Camera indices to try if IP stream fails
# Usually:
#   0 = Laptop built-in webcam (AVOID THIS!)
#   1 = DroidCam virtual camera (YOUR DROIDCAM!)
#   2 = Other external cameras

# Try these indices in order (skipping 0 = laptop webcam)
# Put 1 first since that's confirmed to be DroidCam
CAMERA_INDICES_TO_TRY = [1, 2, 3]

# ============================================================
# DETECTION SETTINGS
# ============================================================

# Minimum resolution to consider as DroidCam (filters out low-res webcams)
MIN_DROIDCAM_WIDTH = 640
MIN_DROIDCAM_HEIGHT = 480

# ============================================================
# USAGE EXAMPLE
# ============================================================
"""
In your scripts, use:

    from droidcam_config import DROIDCAM_URL, CAMERA_INDICES_TO_TRY
    
    # Try IP stream first
    cap = cv2.VideoCapture(DROIDCAM_URL)
    if not cap.isOpened():
        # Try camera indices
        for index in CAMERA_INDICES_TO_TRY:
            cap = cv2.VideoCapture(index)
            if cap.isOpened():
                break
"""

# ============================================================
# TROUBLESHOOTING
# ============================================================
"""
If connection fails:

1. CHECK PHONE IP:
   - Open DroidCam app on phone
   - Note the "WiFi IP" shown on screen
   - Update DROIDCAM_IP above to match

2. CHECK NETWORK:
   - Phone and PC must be on SAME WiFi network
   - Disable VPN if active
   - Check firewall settings

3. TEST CONNECTION:
   - Run: python test_droidcam.py
   - This will test both IP stream and camera indices

4. VERIFY DROIDCAM CLIENT:
   - If using DroidCam Client, it creates a virtual camera
   - Usually appears at index 1 or 2
   - Run: python test_droidcam.py --index 1

5. FIND YOUR PHONE IP:
   Windows:
     - Open DroidCam app on phone
     - Look for "WiFi IP: XXX.XXX.XXX.XXX"
   
   Or check your router's connected devices list
"""

if __name__ == "__main__":
    print("="*60)
    print("DROIDCAM CONFIGURATION")
    print("="*60)
    print(f"\nCurrent settings:")
    print(f"  IP Address: {DROIDCAM_IP}")
    print(f"  Port: {DROIDCAM_PORT}")
    print(f"  Stream URL: {DROIDCAM_URL}")
    print(f"  Fallback indices: {CAMERA_INDICES_TO_TRY}")
    print("\n" + "="*60)
    print("To update:")
    print(f"  1. Open droidcam_config.py in a text editor")
    print(f"  2. Change DROIDCAM_IP to your phone's IP")
    print(f"  3. Save the file")
    print("="*60)
    
    # Quick validation
    print("\nTesting connection...")
    import cv2
    
    print(f"\nTrying IP stream: {DROIDCAM_URL}")
    cap = cv2.VideoCapture(DROIDCAM_URL)
    if cap.isOpened():
        print("  ✓ IP stream works!")
        cap.release()
    else:
        print("  ✗ IP stream failed")
        print(f"\n  Update DROIDCAM_IP in droidcam_config.py")
        print(f"  Current value: {DROIDCAM_IP}")
        print(f"  Check DroidCam app on phone for correct IP")
