import cv2
import time

print("Searching for DroidCam among available cameras...")
print("Close each window to test the next camera")
print("=" * 60)

# Test indices 0-5
for i in range(6):
    print(f"\nTrying camera index {i}...")
    cap = cv2.VideoCapture(i)
    
    if not cap.isOpened():
        print(f"  ✗ Camera {i}: Not available")
        continue
    
    ret, frame = cap.read()
    if not ret:
        print(f"  ✗ Camera {i}: Can't read frame")
        cap.release()
        continue
    
    print(f"  ✓ Camera {i}: Working! Showing preview...")
    print(f"     Resolution: {int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))}x{int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))}")
    print(f"\n     >>> IS THIS YOUR DROIDCAM? <<<")
    print(f"     Close the window to continue testing...")
    
    # Show preview
    window_name = f'Camera {i} - Is this DroidCam?'
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    
    for _ in range(100):  # Show for ~3 seconds or until closed
        ret, frame = cap.read()
        if ret:
            cv2.putText(frame, f"Camera Index {i}", (20, 40), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)
            cv2.putText(frame, "Is this DroidCam?", (20, 90), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
            cv2.imshow(window_name, frame)
        
        if cv2.waitKey(30) & 0xFF == 27:  # ESC to skip
            break
    
    cap.release()
    cv2.destroyAllWindows()
    time.sleep(0.3)

print("\n" + "=" * 60)
print("Testing complete!")
print("Which camera index was DroidCam?")
