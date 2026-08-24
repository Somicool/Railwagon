"""
Test Train Detection in Damage Detector
=========================================

Test that the improved damage detector correctly:
1. Detects when train is NOT in frame (early arrival)
2. Skips damage detection when no train present
3. Only runs damage detection when train is sufficiently visible

This fixes the issue where background objects were being detected as damage.
"""

import cv2
import numpy as np
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, 'railway_dashboard/backend')

from damage_detector import WagonDamageDetector


def test_damage_detector_with_train_detection():
    """Test the damage detector with train detection."""
    
    print("=" * 80)
    print("Testing Improved Damage Detector with Train Detection")
    print("=" * 80)
    
    # Initialize detector with different coverage thresholds
    print("\nTest 1: Standard threshold (15%)")
    detector_standard = WagonDamageDetector(device='cpu', min_train_coverage=0.15)
    
    print("\nTest 2: Strict threshold (25%)")
    detector_strict = WagonDamageDetector(device='cpu', min_train_coverage=0.25)
    
    print("\nTest 3: Relaxed threshold (10%)")
    detector_relaxed = WagonDamageDetector(device='cpu', min_train_coverage=0.10)
    
    # Check if test image exists
    test_image_path = input("\nEnter path to test image (or press Enter to skip): ").strip()
    
    if not test_image_path or not Path(test_image_path).exists():
        print("\nNo valid image provided. Testing with synthetic images...")
        
        # Create synthetic test images
        test_images = create_synthetic_test_images()
        
        for name, image in test_images.items():
            print(f"\n{'='*60}")
            print(f"Testing: {name}")
            print('='*60)
            
            # Test with different thresholds
            for detector_name, detector in [
                ("Standard (15%)", detector_standard),
                ("Strict (25%)", detector_strict),
                ("Relaxed (10%)", detector_relaxed)
            ]:
                print(f"\n{detector_name}:")
                result = detector.detect_damage(image)
                
                print(f"  Train Coverage: {result.get('train_coverage', 0)*100:.1f}%")
                print(f"  Has Damage: {result['has_damage']}")
                print(f"  Damage Count: {result['damage_count']}")
                
                # Save result
                output_path = f"test_output_{name.lower().replace(' ', '_')}_{detector_name.lower().replace(' ', '_').replace('(', '').replace(')', '').replace('%', 'pct')}.jpg"
                if result['annotated_image'] is not None:
                    cv2.imwrite(output_path, result['annotated_image'])
                    print(f"  Saved: {output_path}")
    
    else:
        # Test with actual image
        print(f"\nLoading image: {test_image_path}")
        image = cv2.imread(test_image_path)
        
        if image is None:
            print("Error: Could not load image")
            return
        
        print(f"Image size: {image.shape[1]}x{image.shape[0]}")
        
        # Test with all three detectors
        for detector_name, detector in [
            ("Standard (15%)", detector_standard),
            ("Strict (25%)", detector_strict),
            ("Relaxed (10%)", detector_relaxed)
        ]:
            print(f"\n{'='*60}")
            print(f"Testing with {detector_name}")
            print('='*60)
            
            result = detector.detect_damage(image)
            
            print(f"\nResults:")
            print(f"  Train Coverage: {result.get('train_coverage', 0)*100:.1f}%")
            print(f"  Has Damage: {result['has_damage']}")
            print(f"  Damage Type: {result.get('damage_type', 'None')}")
            print(f"  Confidence: {result['confidence']*100:.1f}%")
            print(f"  Damage Count: {result['damage_count']}")
            
            if result['has_damage'] and 'damages' in result:
                print(f"\n  Detected Damages:")
                for i, damage in enumerate(result['damages']):
                    print(f"    {i+1}. Type: {damage['type']}, Confidence: {damage['confidence']*100:.1f}%")
            
            # Save annotated image
            output_path = f"damage_detection_{detector_name.lower().replace(' ', '_').replace('(', '').replace(')', '').replace('%', 'pct')}.jpg"
            if result['annotated_image'] is not None:
                cv2.imwrite(output_path, result['annotated_image'])
                print(f"\n  Saved annotated image: {output_path}")
    
    print("\n" + "="*80)
    print("Testing Complete!")
    print("="*80)


def create_synthetic_test_images():
    """Create synthetic test images for testing."""
    images = {}
    
    # 1. Empty background (no train)
    bg_only = np.ones((720, 1280, 3), dtype=np.uint8) * 200
    # Add some random background features
    for _ in range(10):
        x, y = np.random.randint(0, 1000), np.random.randint(0, 400)
        w, h = np.random.randint(50, 150), np.random.randint(50, 150)
        color = tuple(np.random.randint(100, 255, 3).tolist())
        cv2.rectangle(bg_only, (x, y), (x+w, y+h), color, -1)
    
    images["Background Only (No Train)"] = bg_only
    
    # 2. Train just entering (small coverage)
    partial_train = bg_only.copy()
    # Add small train slice on edge
    train_color = (60, 180, 220)  # Yellow train
    cv2.rectangle(partial_train, (0, 300), (200, 600), train_color, -1)
    # Add a window
    cv2.rectangle(partial_train, (50, 380), (150, 480), (200, 200, 200), -1)
    
    images["Train Entering (10% Coverage)"] = partial_train
    
    # 3. Train partially visible (medium coverage)
    medium_train = bg_only.copy()
    cv2.rectangle(medium_train, (0, 250), (600, 650), train_color, -1)
    # Add windows
    for x in range(50, 550, 150):
        cv2.rectangle(medium_train, (x, 320), (x+100, 420), (200, 200, 200), -1)
        cv2.rectangle(medium_train, (x, 480), (x+100, 580), (200, 200, 200), -1)
    
    images["Train Partial (40% Coverage)"] = medium_train
    
    # 4. Train fully visible (high coverage)
    full_train = bg_only.copy()
    cv2.rectangle(full_train, (50, 200), (1200, 680), train_color, -1)
    # Add multiple windows
    for x in range(100, 1150, 150):
        cv2.rectangle(full_train, (x, 280), (x+100, 380), (200, 200, 200), -1)
        cv2.rectangle(full_train, (x, 450), (x+100, 550), (200, 200, 200), -1)
    
    images["Train Full (80% Coverage)"] = full_train
    
    return images


if __name__ == "__main__":
    test_damage_detector_with_train_detection()
