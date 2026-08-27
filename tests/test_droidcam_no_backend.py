import cv2

print("Testing cameras WITHOUT DirectShow backend...")
print("=" * 60)

for i in range(10):
    print(f"\n[Device {i}]")
    
    # Try WITHOUT backend specification
    cap = cv2.VideoCapture(i)
    
    if cap.isOpened():
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        backend = cap.getBackendName()
        
        ret, frame = cap.read()
        
        if ret:
            print(f"✓ WORKING: {width}x{height}")
            print(f"  Backend: {backend}")
            print(f"  Frame shape: {frame.shape}")
        else:
            print(f"✓ Opened but no frame")
        
        cap.release()
    else:
        print(f"✗ Not available")

print("\n" + "=" * 60)
