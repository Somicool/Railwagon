"""
Test Camera Stream - Quick diagnostic for DroidCam streaming
=============================================================

This script tests if the camera can be opened and streamed properly.
Run this before starting the dashboard to verify DroidCam is working.
"""
import cv2
import sys
sys.path.insert(0, r'e:\blur\blur')
from droidcam_config import DROIDCAM_URL

print("="*60)
print("CAMERA STREAM TEST")
print("="*60)
print(f"\nTesting camera: {DROIDCAM_URL}")
print(f"Type: {type(DROIDCAM_URL)}\n")

# Try to open camera with default backend first
if isinstance(DROIDCAM_URL, int):
    cap = cv2.VideoCapture(DROIDCAM_URL)
    print(f"Opening camera {DROIDCAM_URL} with default backend...")
    if not cap.isOpened():
        print(f"Default backend failed, trying DSHOW...")
        cap = cv2.VideoCapture(DROIDCAM_URL, cv2.CAP_DSHOW)
else:
    cap = cv2.VideoCapture(DROIDCAM_URL)
    print(f"Opening URL: {DROIDCAM_URL}...")

if not cap.isOpened():
    print("\n❌ FAILED: Could not open camera!")
    print("\nTroubleshooting:")
    print("  1. Make sure DroidCam app is running on your phone")
    print("  2. Make sure DroidCam PC client is running")
    print("  3. Check that they are connected")
    print("  4. Try changing DROIDCAM_URL in droidcam_config.py")
    sys.exit(1)

print("✓ Camera opened successfully!\n")

# Set camera properties
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
cap.set(cv2.CAP_PROP_FPS, 30)

# Test reading frames
print("Testing frame capture (reading 10 frames)...")
success_count = 0
for i in range(10):
    ret, frame = cap.read()
    if ret and frame is not None:
        success_count += 1
        if i == 0:
            print(f"  Frame 1: ✓ Shape: {frame.shape}, Resolution: {frame.shape[1]}x{frame.shape[0]}")
    else:
        print(f"  Frame {i+1}: ❌ Failed to read")

print(f"\nResults: {success_count}/10 frames captured successfully")

if success_count >= 8:
    print("\n✅ EXCELLENT: Camera is working perfectly!")
    print("   The dashboard should work fine.\n")
    
    # Save a test frame
    ret, frame = cap.read()
    if ret:
        cv2.imwrite(r'e:\blur\blur\railway_dashboard\test_camera_frame.jpg', frame)
        print("📷 Test frame saved to: railway_dashboard/test_camera_frame.jpg")
elif success_count >= 5:
    print("\n⚠ WARNING: Camera is working but unstable")
    print("   Some frames failed. Check your connection.")
else:
    print("\n❌ FAILED: Camera is not working properly")
    print("   Too many failed frames. Please check your DroidCam setup.")

# Test continuous streaming
print("\n" + "="*60)
print("LIVE STREAM TEST (Press 'q' to stop)")
print("="*60)
print("This will show the live camera feed in a window.")
print("If you see your camera feed, the dashboard will work!\n")

frame_count = 0
while True:
    ret, frame = cap.read()
    if not ret or frame is None:
        print("Failed to grab frame")
        break
    
    frame_count += 1
    
    # Add frame counter to display
    cv2.putText(frame, f"Frame: {frame_count}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    
    cv2.imshow('Camera Stream Test', frame)
    
    # Press 'q' to quit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

print(f"\n✓ Stream test completed! Total frames: {frame_count}")
print("\nIf the video showed correctly, your dashboard will work fine.")
print("="*60)
