import cv2
import time

print("Testing all camera devices with detailed info...")
print("=" * 60)

for i in range(10):
    print(f"\n[Device {i}]")
    
    # Try with DirectShow backend
    cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
    
    if cap.isOpened():
        # Get camera properties
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        backend = cap.getBackendName()
        
        # Try to read a frame
        ret, frame = cap.read()
        
        if ret:
            print(f"✓ WORKING: {width}x{height} @ {fps}fps")
            print(f"  Backend: {backend}")
            print(f"  Frame captured: {frame.shape}")
            
            # Check if it's grayscale or has color variance (to identify which camera)
            mean_color = frame.mean(axis=(0,1))
            print(f"  Mean BGR: {mean_color}")
        else:
            print(f"✓ Opened but couldn't read frame")
        
        cap.release()
    else:
        print(f"✗ Not available")
    
    time.sleep(0.2)

print("\n" + "=" * 60)
print("Scan complete!")
