"""
Test DroidCam Connection
========================

Comprehensive test to find and verify DroidCam connection.

This script:
1. Lists all available cameras
2. Tests DroidCam IP stream
3. Helps you identify which camera is DroidCam

No processing, just camera detection!
"""

import cv2
import sys


def test_ip_stream(ip="192.168.1.100", port=4747):
    """Test DroidCam IP stream connection."""
    url = f"http://{ip}:{port}/video"
    print(f"\n[TEST 1] DroidCam IP Stream")
    print(f"  URL: {url}")
    print(f"  Attempting connection...")
    
    cap = cv2.VideoCapture(url)
    
    if not cap.isOpened():
        print(f"  ✗ Failed to connect to {url}")
        print(f"\n  How to fix:")
        print(f"    1. Check DroidCam app is running on phone")
        print(f"    2. Note the IP address shown in DroidCam app")
        print(f"    3. Run: python test_droidcam.py --ip YOUR_IP")
        print(f"    4. Example: python test_droidcam.py --ip 192.168.1.50")
        return False
    
    # Try to read a frame
    ret, frame = cap.read()
    if not ret:
        print(f"  ✗ Connected but can't read frames")
        cap.release()
        return False
    
    # Get properties
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    print(f"  ✓ SUCCESS! DroidCam IP stream working")
    print(f"  Resolution: {width}x{height}")
    print(f"  FPS: {fps if fps > 0 else 'Unknown'}")
    
    # Show preview
    print(f"\n  Showing preview... Press 'q' to continue")
    
    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        frame_count += 1
        cv2.putText(frame, f"DroidCam IP Stream - Frame {frame_count}", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, f"{url}", 
                   (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(frame, "Press 'q' to continue", 
                   (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
        
        cv2.imshow('DroidCam IP Test', frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
    
    print(f"  ✓ IP stream test completed ({frame_count} frames)")
    return True


def list_all_cameras(max_index=5):
    """List all available cameras."""
    print(f"\n[TEST 2] Scanning Camera Indices (0-{max_index})")
    print("="*60)
    
    available_cameras = []
    
    for index in range(max_index + 1):
        print(f"\nCamera index {index}:")
        cap = cv2.VideoCapture(index)
        
        if not cap.isOpened():
            print(f"  ✗ Not available")
            continue
        
        # Try to read a frame
        ret, frame = cap.read()
        if not ret:
            print(f"  ✗ Can't read frames")
            cap.release()
            continue
        
        # Get properties
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        print(f"  ✓ Available")
        print(f"  Resolution: {width}x{height}")
        print(f"  FPS: {fps if fps > 0 else 'Unknown'}")
        
        # Guess camera type
        if width == 640 and height == 480 and index == 0:
            camera_type = "Likely LAPTOP WEBCAM"
        elif width >= 1280:
            camera_type = "Likely PHONE (DroidCam)"
        else:
            camera_type = "Unknown"
        
        print(f"  Type: {camera_type}")
        
        available_cameras.append({
            'index': index,
            'width': width,
            'height': height,
            'fps': fps,
            'type': camera_type
        })
        
        cap.release()
    
    return available_cameras


def test_specific_camera(camera_index):
    """Test a specific camera with live preview."""
    print(f"\n[TEST 3] Testing Camera Index {camera_index}")
    print("="*60)
    
    cap = cv2.VideoCapture(camera_index)
    
    if not cap.isOpened():
        print(f"  ✗ Camera {camera_index} not available")
        return False
    
    # Get properties
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    print(f"  ✓ Camera {camera_index} opened")
    print(f"  Resolution: {width}x{height}")
    print(f"  FPS: {fps if fps > 0 else 'Unknown'}")
    print(f"\n  Showing live preview... Press 'q' to stop")
    
    frame_count = 0
    
    try:
        while True:
            ret, frame = cap.read()
            
            if not ret:
                print("\n  ⚠ Warning: Failed to read frame")
                continue
            
            frame_count += 1
            
            # Add info overlay
            cv2.putText(frame, f"Camera {camera_index} - Frame {frame_count}", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(frame, f"Resolution: {width}x{height}", 
                       (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            cv2.putText(frame, "Press 'q' to stop", 
                       (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
            
            cv2.imshow(f'Camera {camera_index} Test', frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                print(f"\n  [Stopped by user]")
                break
    
    except KeyboardInterrupt:
        print("\n  [Keyboard interrupt]")
    
    finally:
        cap.release()
        cv2.destroyAllWindows()
        print(f"  ✓ Test completed ({frame_count} frames read)")
        return True


def main():
    """Main test flow."""
    print("="*60)
    print("DROIDCAM COMPREHENSIVE TEST")
    print("="*60)
    
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description='Test DroidCam connection')
    parser.add_argument('--ip', type=str, default='192.168.1.100',
                       help='DroidCam phone IP address (default: 192.168.1.100)')
    parser.add_argument('--port', type=int, default=4747,
                       help='DroidCam port (default: 4747)')
    parser.add_argument('--index', type=int, default=None,
                       help='Test specific camera index only')
    args = parser.parse_args()
    
    # Test specific camera if requested
    if args.index is not None:
        success = test_specific_camera(args.index)
        if success:
            print("\n" + "="*60)
            print(f"✓ Camera {args.index} is working!")
            print("="*60)
            print("\nTo use this camera in your script:")
            print(f"  cap = cv2.VideoCapture({args.index})")
            print("="*60)
        return
    
    # Full test sequence
    print("\nThis test will:")
    print("  1. Try DroidCam IP stream connection")
    print("  2. Scan all camera indices")
    print("  3. Help you identify which is DroidCam")
    print("="*60)
    
    # Test 1: IP Stream
    ip_success = test_ip_stream(args.ip, args.port)
    
    # Test 2: List cameras
    cameras = list_all_cameras()
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    if ip_success:
        print(f"\n✓ DroidCam IP stream works!")
        print(f"  URL: http://{args.ip}:{args.port}/video")
        print(f"\n  Use this in your script:")
        print(f"    cap = cv2.VideoCapture('http://{args.ip}:{args.port}/video')")
    else:
        print(f"\n✗ DroidCam IP stream not working")
        print(f"  Check phone IP address in DroidCam app")
    
    if cameras:
        print(f"\n✓ Found {len(cameras)} camera(s):")
        for cam in cameras:
            print(f"\n  Camera {cam['index']}:")
            print(f"    Resolution: {cam['width']}x{cam['height']}")
            print(f"    Type: {cam['type']}")
            
            if 'PHONE' in cam['type'] or 'DroidCam' in cam['type']:
                print(f"    ⭐ RECOMMENDED: Use this for DroidCam")
                print(f"\n    Use this in your script:")
                print(f"      cap = cv2.VideoCapture({cam['index']})")
    else:
        print("\n✗ No cameras found!")
    
    print("\n" + "="*60)
    print("NEXT STEPS")
    print("="*60)
    
    if ip_success:
        print("\n✓ Your DroidCam is working via IP stream!")
        print("  This is the BEST method (most reliable)")
        print(f"\n  Update your script:")
        print(f"    1. Open live_simple_control.py")
        print(f"    2. Find: droidcam_ip = '192.168.1.100'")
        print(f"    3. Change to: droidcam_ip = '{args.ip}'")
    else:
        droidcam_cameras = [c for c in cameras if 'PHONE' in c['type']]
        if droidcam_cameras:
            best_cam = droidcam_cameras[0]
            print(f"\n✓ Use Camera Index {best_cam['index']} for DroidCam")
            print(f"  This camera is likely your phone ({best_cam['width']}x{best_cam['height']})")
            print(f"\n  Your laptop webcam is probably index 0")
            print(f"  Your DroidCam is probably index {best_cam['index']}")
        else:
            print("\n⚠ Could not identify DroidCam automatically")
            print("  Try testing each camera manually:")
            for cam in cameras:
                print(f"    python test_droidcam.py --index {cam['index']}")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    main()
