import cv2

print("Scanning for camera devices...")
for i in range(10):
    cap = cv2.VideoCapture(i)
    if cap.isOpened():
        ret, frame = cap.read()
        if ret:
            print(f"✓ Device {i}: Working ({frame.shape[1]}x{frame.shape[0]})")
        else:
            print(f"✓ Device {i}: Opened but no frame")
        cap.release()
    else:
        print(f"✗ Device {i}: Not available")
