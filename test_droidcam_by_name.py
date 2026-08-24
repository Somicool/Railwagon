import cv2
import subprocess
import json

# Try to get camera list using ffmpeg (if available)
print("Attempting to list DirectShow video devices...")
try:
    result = subprocess.run(
        ['ffmpeg', '-list_devices', 'true', '-f', 'dshow', '-i', 'dummy'],
        capture_output=True,
        text=True
    )
    print(result.stdout)
except FileNotFoundError:
    print("ffmpeg not found")

print("\n" + "=" * 60)
print("Trying to open DroidCam by name...")

# Try opening by device name
device_names = [
    "DroidCam Video",
    "DroidCam Source",
    "video=DroidCam Video",
    "DroidCam"
]

for name in device_names:
    print(f"\nTrying: {name}")
    cap = cv2.VideoCapture(name, cv2.CAP_DSHOW)
    
    if cap.isOpened():
        ret, frame = cap.read()
        if ret:
            print(f"  ✓ SUCCESS! Got frame: {frame.shape}")
            cap.release()
            break
        else:
            print(f"  ✗ Opened but no frame")
        cap.release()
    else:
        print(f"  ✗ Couldn't open")
