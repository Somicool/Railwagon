import cv2

ip = "192.168.1.5"
port = 4747

# Test 2: Try different video URLs
urls_to_try = [
    f"http://{ip}:{port}/video",
    f"http://{ip}:{port}/mjpegfeed",
    f"http://{ip}:{port}/cam/1/stream",
]

print("\nTrying different video URLs...")
for url in urls_to_try:
    print(f"\nTesting: {url}")
    cap = cv2.VideoCapture(url)
    if cap.isOpened():
        ret, frame = cap.read()
        if ret:
            print(f"  ✓ SUCCESS! This URL works: {url}")
            print(f"  Frame size: {frame.shape}")
            cap.release()
            break
        else:
            print(f"  ✗ Opened but can't read frames")
            cap.release()
    else:
        print(f"  ✗ Failed to open")

print("\n" + "="*50)
print("If none worked, make sure:")
print("1. DroidCam app is open on your phone")
print("2. Phone shows 'Connected' or 'Start Server' is clicked")
print("3. Phone and PC are on same WiFi network")
print("4. Windows Firewall isn't blocking the connection")
