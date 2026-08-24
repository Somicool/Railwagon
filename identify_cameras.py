import cv2
import subprocess

print("Identifying camera devices...\n")

# Method 1: Check DirectShow devices using ffmpeg
try:
    result = subprocess.run(
        ['ffmpeg', '-list_devices', 'true', '-f', 'dshow', '-i', 'dummy'],
        capture_output=True,
        text=True,
        stderr=subprocess.STDOUT
    )
    print("=== DirectShow Devices (from ffmpeg) ===")
    print(result.stdout)
except:
    print("ffmpeg not available, skipping DirectShow device list\n")

# Method 2: Test each camera index
print("\n=== Testing Camera Indices ===")
for i in range(3):
    cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
    if cap.isOpened():
        # Try to get camera backend name
        backend = cap.getBackendName()
        width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        
        # Capture a test frame
        ret, frame = cap.read()
        
        print(f"\n✓ Device {i}:")
        print(f"  Backend: {backend}")
        print(f"  Resolution: {int(width)}x{int(height)}")
        print(f"  Frame capture: {'SUCCESS' if ret else 'FAILED'}")
        
        # Try to read camera name (Windows specific)
        try:
            import win32api
            import win32con
            # This is a placeholder - actual implementation would need more work
        except:
            pass
        
        cap.release()
    else:
        print(f"\n✗ Device {i}: Not available")

print("\n=== Instructions ===")
print("Look for 'DroidCam' in the device names above.")
print("If you see multiple devices, DroidCam typically has 640x480 resolution.")
print("Your laptop webcam likely has higher resolution (e.g., 1280x720).")
