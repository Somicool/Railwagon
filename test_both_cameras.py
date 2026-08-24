import cv2
import time

print("Testing camera 0...")
cap0 = cv2.VideoCapture(0, cv2.CAP_DSHOW)
if cap0.isOpened():
    ret, frame = cap0.read()
    if ret:
        cv2.imshow("Camera 0", frame)
        cv2.waitKey(2000)
        print("✓ Camera 0 working")
    cap0.release()
else:
    print("✗ Camera 0 not available")

print("\nTesting camera 1...")
cap1 = cv2.VideoCapture(1, cv2.CAP_DSHOW)
if cap1.isOpened():
    ret, frame = cap1.read()
    if ret:
        cv2.imshow("Camera 1", frame)
        cv2.waitKey(2000)
        print("✓ Camera 1 working")
    cap1.release()
else:
    print("✗ Camera 1 not available")

cv2.destroyAllWindows()
print("\nWhich camera showed your PHONE? That's DroidCam!")
