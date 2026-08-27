import cv2
import requests

droidcam_ip = "192.168.1.5"
droidcam_port = 4747

# Test URLs
urls_to_test = [
    f"http://{droidcam_ip}:{droidcam_port}/video",
    f"http://{droidcam_ip}:{droidcam_port}/mjpegfeed",
    f"http://{droidcam_ip}:{droidcam_port}/cam/1/stream",
    f"http://{droidcam_ip}:{droidcam_port}/",
]

print(f"Testing DroidCam URLs for {droidcam_ip}:{droidcam_port}")
print("=" * 70)

# First, test if DroidCam server is reachable
print("\n[1] Testing HTTP connectivity...")
for url in urls_to_test:
    try:
        response = requests.get(url, timeout=2, stream=True)
        print(f"  {url}")
        print(f"    Status: {response.status_code}")
        print(f"    Content-Type: {response.headers.get('Content-Type', 'Unknown')}")
        response.close()
    except requests.exceptions.Timeout:
        print(f"  {url} - TIMEOUT")
    except requests.exceptions.ConnectionError:
        print(f"  {url} - CONNECTION REFUSED")
    except Exception as e:
        print(f"  {url} - ERROR: {e}")

print("\n[2] Testing OpenCV VideoCapture...")
for url in urls_to_test:
    print(f"\nTrying: {url}")
    cap = cv2.VideoCapture(url)
    
    if cap.isOpened():
        print(f"  ✓ Opened!")
        ret, frame = cap.read()
        if ret:
            print(f"  ✓ Frame captured: {frame.shape}")
        else:
            print(f"  ✗ Couldn't read frame")
        cap.release()
    else:
        print(f"  ✗ Couldn't open")

print("\n" + "=" * 70)
print("Test complete!")
