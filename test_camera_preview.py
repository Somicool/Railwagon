import cv2

print("Testing cameras - press 'q' to switch between cameras")
print("Check which one shows your PHONE camera (from DroidCam)")
print("")

for device_id in [0, 1]:
    print(f"\n========================================")
    print(f"Testing Device {device_id}")
    print(f"========================================")
    print("Press 'q' to go to next camera")
    
    cap = cv2.VideoCapture(device_id)
    if not cap.isOpened():
        print(f"Device {device_id} not available")
        continue
    
    window_name = f"Device {device_id} - Is this your PHONE camera?"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print(f"Failed to read from device {device_id}")
            break
        
        # Add text to frame
        text = f"Device {device_id} - Press 'q' for next camera"
        cv2.putText(frame, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 
                    0.7, (0, 255, 0), 2)
        
        cv2.imshow(window_name, frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()

print("\n\nWhich device showed your PHONE camera?")
print("Device 0 or Device 1?")
