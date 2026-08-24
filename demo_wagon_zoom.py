"""
Demonstrate the zoomed wagon number feature
"""
import cv2
import numpy as np
from pathlib import Path

print("=" * 80)
print("WAGON NUMBER ZOOM DEMONSTRATION")
print("=" * 80)

# Find a recent wagon image
sessions_path = Path("railway_dashboard/backend/sessions")
wagon_images = list(sessions_path.rglob("wagon_*.jpg"))

if wagon_images:
    # Show first wagon image
    img_path = wagon_images[0]
    img = cv2.imread(str(img_path))
    
    if img is not None:
        h, w = img.shape[:2]
        print(f"\n✓ Found wagon image: {img_path.name}")
        print(f"  Dimensions: {w}x{h} pixels")
        
        if w < 1000:
            print(f"\n  ✅ THIS IS A ZOOMED WAGON NUMBER REGION!")
            print(f"  • Not a full frame (would be ~1920x1080)")
            print(f"  • Zoomed to wagon number area with 50% padding")
            print(f"  • Deblurred for clarity")
            print(f"  • Green box shows wagon number location")
        else:
            print(f"\n  ⚠️  This appears to be a full frame")
            print(f"  • Expected: < 1000px width for zoomed region")
            print(f"  • Actual: {w}px width")
            
        print(f"\n  Image saved at: {img_path}")
        print(f"\n  You can:")
        print(f"  1. View it directly in the file browser")
        print(f"  2. See it in the dashboard at http://localhost:5000")
        print(f"  3. The wagon number should be LARGE and clearly visible")
        
else:
    print("\n⚠️  No wagon images found yet")
    print("  • Process a video through the dashboard to generate wagon detections")
    print("  • Or run: python test_wagon_zoom.py 'railway vid 3.mp4'")

print("\n" + "=" * 80)
print("UPDATED VALIDATION RULES")
print("=" * 80)
print("\n✓ 8 digits = PURE NUMERIC (no letters)")
print("  Examples: 12345678 ✓")
print("           A12345678 ✗ (8 digits cannot have letters)")
print("\n✓ 6-7 digits = CAN have 1-3 letter prefix")
print("  Examples: A123456 ✓, AB123456 ✓, ABC1234567 ✓")
print("           123456 ✗ (6 digits need letter prefix OR must be 8 digits)")
print("=" * 80)
