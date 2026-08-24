import cv2

print("Opening camera 1...")
cap = cv2.VideoCapture(1)

if not cap.isOpened():
    print("ERROR: Cannot open camera 1")
    exit()

print("Camera 1 opened successfully!")
print("Press 'q' to quit")
print("\nLook at the video - is this your:")
print("  A) DroidCam (phone camera)")
print("  B) Laptop webcam")

while True:
    ret, frame = cap.read()
    if not ret:
        print("ERROR: Can't receive frame")
        break
    
    # Add text to frame
    cv2.putText(frame, "Camera Index 1", (10, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    cv2.putText(frame, "Is this DroidCam or Laptop?", (10, 70), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
    
    cv2.imshow('Camera 1 Test', frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
print("Test complete!")
