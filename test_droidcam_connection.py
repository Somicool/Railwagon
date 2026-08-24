"""
Quick DroidCam Connection Test
===============================

Run this first to verify your DroidCam connection works.
"""

import cv2

# Your DroidCam URL
DROIDCAM_URL = "http://192.168.1.6:4747/video"

print("Testing DroidCam connection...")
print(f"URL: {DROIDCAM_URL}")
print()

# Try to connect
cap = cv2.VideoCapture(DROIDCAM_URL)

if not cap.isOpened():
    print("❌ FAILED to connect to DroidCam")
    print()
    print("Troubleshooting:")
    print("1. Open DroidCam app on your phone")
    print("2. Check the IP address shown in the app")
    print("3. Update DROIDCAM_URL in this script")
    print("4. Make sure phone and computer are on same WiFi")
    print("5. Try accessing the URL in a web browser:")
    print(f"   {DROIDCAM_URL}")
else:
    print("✓ Connected successfully!")
    
    # Read one frame
    ret, frame = cap.read()
    
    if ret:
        h, w = frame.shape[:2]
        print(f"✓ Frame received: {w}x{h} pixels")
        print()
        print("Showing preview window...")
        print("Press 'q' to quit")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            cv2.imshow("DroidCam Test", frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    else:
        print("❌ Connected but failed to read frame")
    
    cap.release()
    cv2.destroyAllWindows()

print()
print("Test complete!")
