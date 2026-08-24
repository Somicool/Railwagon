"""
Test Background ROI Filtering
==============================

Tests that the improved ROI damage detector correctly:
1. Rejects background objects (buildings, poles, platforms)
2. Accepts train ROIs (windows, doors)
3. Shows detailed validation reasoning

Usage:
    python test_background_filtering.py <image_path>
"""

import cv2
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, 'railway_dashboard/backend')

from roi_inspection_pipeline import ROIInspectionPipeline
from roi_damage_detector import ROIDamageDetector


def test_background_filtering(image_path):
    """Test the background ROI filtering."""
    
    print("=" * 80)
    print("Testing Background ROI Filtering")
    print("=" * 80)
    
    # Load image
    if not Path(image_path).exists():
        print(f"Error: Image not found: {image_path}")
        return
    
    image = cv2.imread(image_path)
    if image is None:
        print(f"Error: Could not load image: {image_path}")
        return
    
    print(f"\nImage loaded: {image.shape[1]}x{image.shape[0]}")
    
    # Test 1: With train context validation (default)
    print("\n" + "=" * 80)
    print("TEST 1: With Train Context Validation (RECOMMENDED)")
    print("=" * 80)
    
    pipeline_with_validation = ROIInspectionPipeline()
    results_validated = pipeline_with_validation.process_frame(image, frame_id='test_001')
    
    print(f"\nResults:")
    print(f"  Total ROIs detected: {results_validated['roi_detections']}")
    print(f"  Damage detections (validated): {len(results_validated['damage_detections'])}")
    
    if results_validated['damage_detections']:
        print(f"\n  Accepted Damage Detections:")
        for i, dmg in enumerate(results_validated['damage_detections']):
            validation = dmg.get('validation', {})
            print(f"    {i+1}. Type: {dmg['damage_type']}, " 
                  f"Valid: {validation.get('is_train_roi')}, "
                  f"Confidence: {dmg['confidence']:.2f}")
    
    # Save annotated result
    output_path_validated = 'test_output_with_validation.jpg'
    if 'annotated_frame' in results_validated:
        cv2.imwrite(output_path_validated, results_validated['annotated_frame'])
        print(f"\n  Saved: {output_path_validated}")
    
    # Test 2: Without train context validation (for comparison)
    print("\n" + "=" * 80)
    print("TEST 2: Without Train Context Validation (FOR COMPARISON)")
    print("=" * 80)
    print("This shows what would happen without background filtering...")
    
    # Create detector without validation
    from roi_detector import ROIDetector
    from roi_enhancer import ROIEnhancer
    from ocr_pipeline import OCRPipeline
    
    detector_no_validation = ROIDamageDetector(
        sensitivity='medium',
        require_train_context=False  # Disable validation
    )
    
    # Run detection manually
    roi_detector = ROIDetector()
    detections = roi_detector.detect_rois(image)
    
    print(f"\n  Total ROIs detected: {len(detections)}")
    
    damage_count_no_validation = 0
    for i, det in enumerate(detections):
        if det['class'] in ['window', 'door']:
            result = detector_no_validation.analyze_damage(det['crop'], det['class'])
            if result['has_damage']:
                damage_count_no_validation += 1
                print(f"    ROI #{i+1} ({det['class']}): DAMAGE - {result['damage_type']}")
    
    print(f"\n  Damage detections (no validation): {damage_count_no_validation}")
    
    # Summary
    print("\n" + "=" * 80)
    print("COMPARISON SUMMARY")
    print("=" * 80)
    print(f"  Total ROIs detected: {results_validated['roi_detections']}")
    print(f"  Damage with validation: {len(results_validated['damage_detections'])}")
    print(f"  Damage without validation: {damage_count_no_validation}")
    
    if damage_count_no_validation > len(results_validated['damage_detections']):
        filtered = damage_count_no_validation - len(results_validated['damage_detections'])
        print(f"\n  ✅ Background filtering removed {filtered} false positive(s)!")
    else:
        print(f"\n  No false positives detected in this image")
    
    print("\n" + "=" * 80)


def create_test_image():
    """Create a synthetic test image with train and background."""
    print("Creating synthetic test image...")
    
    # Create image
    img = np.ones((720, 1280, 3), dtype=np.uint8) * 180
    
    # Add sky
    img[0:250, :] = [180, 200, 220]
    
    # Add background buildings (top part of image)
    # These should be REJECTED by validation
    cv2.rectangle(img, (50, 80), (200, 250), (100, 120, 140), -1)  # Building
    cv2.rectangle(img, (70, 120), (120, 180), (200, 220, 240), -1)  # Window
    cv2.rectangle(img, (140, 120), (180, 180), (200, 220, 240), -1)  # Window
    
    # Add pole (should be rejected - high edge density)
    cv2.rectangle(img, (900, 50), (920, 600), (80, 80, 80), -1)
    
    # Add train (lower part of image)
    # These should be ACCEPTED by validation
    train_color = (60, 180, 220)  # Yellow train
    cv2.rectangle(img, (100, 350), (1100, 650), train_color, -1)
    
    # Add train windows (should be accepted)
    for x in range(150, 1000, 200):
        cv2.rectangle(img, (x, 400), (x+120, 500), (200, 210, 220), -1)
        cv2.rectangle(img, (x, 520), (x+120, 600), (200, 210, 220), -1)
    
    # Add horizontal lines on train
    cv2.line(img, (100, 380), (1100, 380), (40, 160, 200), 3)
    cv2.line(img, (100, 620), (1100, 620), (40, 160, 200), 3)
    
    # Save
    output_path = 'synthetic_test_image.jpg'
    cv2.imwrite(output_path, img)
    print(f"Saved: {output_path}")
    return output_path


if __name__ == "__main__":
    import numpy as np
    
    if len(sys.argv) > 1:
        # Use provided image
        image_path = sys.argv[1]
    else:
        # Create synthetic test image
        print("No image provided - creating synthetic test image...\n")
        image_path = create_test_image()
        print()
    
    test_background_filtering(image_path)
