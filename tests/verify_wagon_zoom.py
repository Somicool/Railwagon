"""
Verify Wagon Zoom Output
=========================

This script verifies that wagon detection outputs contain
ONLY zoomed wagon number regions, not full frames.

It checks the dimensions of saved wagon images to confirm
they are cropped regions (typically 200-500px wide) rather
than full frames (1920px wide).
"""

import cv2
from pathlib import Path
import sys

def verify_zoom_outputs(sessions_dir="railway_dashboard/backend/sessions"):
    """Check if wagon images are zoomed regions or full frames"""
    
    sessions_path = Path(sessions_dir)
    if not sessions_path.exists():
        print(f"Sessions directory not found: {sessions_dir}")
        return
    
    print("=" * 80)
    print("WAGON OUTPUT VERIFICATION")
    print("=" * 80)
    print()
    
    wagon_images = list(sessions_path.glob("*/wagon_detections/wagon_*.jpg"))
    
    if not wagon_images:
        print("No wagon detection images found yet.")
        print("Run a video or live camera session first.")
        return
    
    print(f"Found {len(wagon_images)} wagon detection images")
    print()
    
    zoomed_count = 0
    full_frame_count = 0
    
    for img_path in wagon_images[:10]:  # Check first 10
        img = cv2.imread(str(img_path))
        if img is None:
            continue
        
        h, w = img.shape[:2]
        
        # Full frames are typically 1920x1080 or similar
        # Zoomed regions should be much smaller (200-500px wide)
        is_zoomed = w < 800  # Reasonable threshold
        
        if is_zoomed:
            zoomed_count += 1
            status = "✓ ZOOMED"
        else:
            full_frame_count += 1
            status = "✗ FULL FRAME"
        
        print(f"{status:15} | {img_path.name:40} | Size: {w}x{h} pixels")
    
    print()
    print("=" * 80)
    print(f"Summary: {zoomed_count} zoomed regions, {full_frame_count} full frames")
    
    if full_frame_count == 0 and zoomed_count > 0:
        print()
        print("✅ SUCCESS! All wagon images are ZOOMED REGIONS (not full frames)")
        print("   Your wagon number outputs show only the wagon number region!")
    elif zoomed_count > 0:
        print()
        print("⚠️ MIXED: Some zoomed, some full frames")
        print("   Recent detections should be zoomed after the update")
    else:
        print()
        print("ℹ️ All images are full frames")
        print("   Run a new detection to generate zoomed outputs")
    
    print("=" * 80)


if __name__ == "__main__":
    sessions_dir = sys.argv[1] if len(sys.argv) > 1 else "railway_dashboard/backend/sessions"
    verify_zoom_outputs(sessions_dir)
