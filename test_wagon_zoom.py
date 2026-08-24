"""
Wagon Number Zoom & Deblur Test
=================================

This script demonstrates the new wagon number detection that:
1. Detects wagon number region using OCR
2. Zooms/crops to that specific region (with 30% padding)
3. Deblurs the zoomed region for sharper text
4. Saves only the zoomed+deblurred wagon number (not full image)

This makes it much easier to see and verify the wagon number!

Usage:
    python test_wagon_zoom.py <image_or_video_path>
    
Example:
    python test_wagon_zoom.py "railway vid 3.mp4"
    python test_wagon_zoom.py wagon_image.jpg
"""

import cv2
import numpy as np
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent / 'railway_dashboard' / 'backend'))

from inspection_processor import InspectionProcessor


def test_wagon_zoom(input_path, output_dir="wagon_zoom_test"):
    """Test wagon number zoom and deblur functionality"""
    
    print("=" * 80)
    print("WAGON NUMBER ZOOM & DEBLUR TEST")
    print("=" * 80)
    print(f"\nInput: {input_path}")
    print(f"Output: {output_dir}/\n")
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Initialize processor
    processor = InspectionProcessor(camera_index=0)
    
    # Check if video or image
    if input_path.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
        print("Processing VIDEO...")
        process_video(processor, input_path, output_path)
    else:
        print("Processing IMAGE...")
        process_image(processor, input_path, output_path)
    
    print("\n" + "=" * 80)
    print("PROCESSING COMPLETE!")
    print("=" * 80)
    print(f"\nCheck the output directory: {output_dir}/")
    print("\nYou should see:")
    print("  - Original full frames")
    print("  - Zoomed wagon number regions (cropped)")
    print("  - Deblurred wagon numbers (easy to read!)")
    print()


def process_image(processor, image_path, output_path):
    """Process a single image"""
    
    # Read image
    image = cv2.imread(image_path)
    if image is None:
        print(f"ERROR: Cannot read image: {image_path}")
        return
    
    print(f"Image size: {image.shape[1]}x{image.shape[0]} pixels")
    
    # Save original
    cv2.imwrite(str(output_path / "original.jpg"), image)
    
    # Enhance if dark
    enhanced = processor._enhance_low_light(image)
    
    # Deblur full image first
    deblurred_full = processor._deblur_image(enhanced)
    cv2.imwrite(str(output_path / "deblurred_full.jpg"), deblurred_full)
    
    # Detect wagon number and get ZOOMED region
    wagon_number, zoomed_region = processor._detect_wagon_number_with_annotation(deblurred_full)
    
    if wagon_number:
        print(f"\n✓ DETECTED WAGON NUMBER: {wagon_number}")
        
        if zoomed_region is not None:
            # Save the zoomed+deblurred wagon number region
            cv2.imwrite(str(output_path / f"wagon_{wagon_number}_ZOOMED.jpg"), zoomed_region)
            print(f"✓ Saved zoomed region: {zoomed_region.shape[1]}x{zoomed_region.shape[0]} pixels")
            print(f"  File: wagon_{wagon_number}_ZOOMED.jpg")
        else:
            print("⚠ Wagon number detected but no zoomed region created")
    else:
        print("\n✗ No wagon number detected")


def process_video(processor, video_path, output_path):
    """Process video and extract zoomed wagon numbers"""
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"ERROR: Cannot open video: {video_path}")
        return
    
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    print(f"Video: {total_frames} frames @ {fps:.1f} fps")
    print(f"Processing every 10th frame...\n")
    
    frame_count = 0
    wagon_count = 0
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        frame_count += 1
        
        # Process every 10th frame
        if frame_count % 10 != 0:
            continue
        
        print(f"Frame {frame_count}/{total_frames}...", end=" ")
        
        # Enhance and deblur
        enhanced = processor._enhance_low_light(frame)
        deblurred = processor._deblur_image(enhanced)
        
        # Detect wagon number and get ZOOMED region
        wagon_number, zoomed_region = processor._detect_wagon_number_with_annotation(deblurred)
        
        if wagon_number and zoomed_region is not None:
            wagon_count += 1
            # Save zoomed+deblurred wagon number
            filename = f"frame_{frame_count:06d}_wagon_{wagon_number}_ZOOMED.jpg"
            cv2.imwrite(str(output_path / filename), zoomed_region)
            print(f"✓ DETECTED: {wagon_number} (saved zoomed region)")
        else:
            print("No wagon number")
    
    cap.release()
    
    print(f"\n" + "-" * 80)
    print(f"Summary: Found {wagon_count} wagon numbers in {frame_count} frames")
    print(f"Detection rate: {wagon_count/frame_count*100:.1f}%")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_wagon_zoom.py <image_or_video_path>")
        print("\nExamples:")
        print('  python test_wagon_zoom.py "railway vid 3.mp4"')
        print('  python test_wagon_zoom.py wagon_image.jpg')
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "wagon_zoom_test"
    
    if not Path(input_path).exists():
        print(f"ERROR: File not found: {input_path}")
        sys.exit(1)
    
    test_wagon_zoom(input_path, output_dir)
