"""
Quick diagnostic to test DroidCam connection
"""
import cv2
import sys
sys.path.insert(0, r'C:\Users\Soham\OneDrive\Desktop\blur')
from droidcam_config import DROIDCAM_URL

print(f"Testing DroidCam connection...")
print(f"DROIDCAM_URL: {DROIDCAM_URL}")
print(f"Type: {type(DROIDCAM_URL)}")

# Try to open camera
cap = cv2.VideoCapture(DROIDCAM_URL)

if not cap.isOpened():
    print("❌ Failed to open camera!")
    print("Make sure:")
    print("  1. DroidCam app is running on your phone")
    print("  2. DroidCam PC client is running")
    print("  3. They are connected")
else:
    print("✓ Camera opened successfully!")
    
    # Try to read a frame
    ret, frame = cap.read()
    
    if ret:
        print(f"✓ Frame captured successfully!")
        print(f"  Frame shape: {frame.shape}")
        print(f"  Resolution: {frame.shape[1]}x{frame.shape[0]}")
        
        # Save a test frame
        cv2.imwrite(r'C:\Users\Soham\OneDrive\Desktop\blur\railway_dashboard\test_frame.jpg', frame)
        print("✓ Test frame saved to railway_dashboard/test_frame.jpg")
    else:
        print("❌ Failed to capture frame!")
    
    cap.release()

print("\nDiagnostic complete!")
