"""
Quick test to verify damage detection works in live processors
"""
import sys
from pathlib import Path
import cv2
import numpy as np

print("="*70)
print("TESTING LIVE DAMAGE DETECTION")
print("="*70)

# Test 1: Import damage detector
print("\n[TEST 1] Importing damage detector...")
try:
    backend_path = Path(__file__).parent / 'railway_dashboard' / 'backend'
    sys.path.insert(0, str(backend_path))
    from damage_detector import WagonDamageDetector
    print("✓ Import successful")
except Exception as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)

# Test 2: Initialize with low threshold (like live processors)
print("\n[TEST 2] Initializing damage detector (1% threshold)...")
try:
    detector = WagonDamageDetector(device='cpu', min_train_coverage=0.01)
    print("✓ Initialization successful")
except Exception as e:
    print(f"✗ Initialization failed: {e}")
    sys.exit(1)

# Test 3: Test with various images
print("\n[TEST 3] Testing damage detection on sample images...")

# Create test images
test_cases = [
    ("Empty black frame", np.zeros((480, 640, 3), dtype=np.uint8)),
    ("Random noise", np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)),
    ("White rectangle (simulated wagon)", None),
]

# Create a simple wagon-like image
wagon_img = np.ones((480, 640, 3), dtype=np.uint8) * 128
# Add window-like rectangles
cv2.rectangle(wagon_img, (100, 150), (250, 300), (200, 200, 200), -1)
cv2.rectangle(wagon_img, (300, 150), (450, 300), (200, 200, 200), -1)
# Add some edge details
cv2.rectangle(wagon_img, (100, 150), (250, 300), (50, 50, 50), 3)
cv2.rectangle(wagon_img, (300, 150), (450, 300), (50, 50, 50), 3)
# Add horizontal lines (train-like)
cv2.line(wagon_img, (0, 350), (640, 350), (100, 100, 100), 2)
cv2.line(wagon_img, (0, 130), (640, 130), (100, 100, 100), 2)
test_cases[2] = ("Simulated wagon", wagon_img)

for name, img in test_cases:
    print(f"\n  Testing: {name}")
    try:
        result = detector.detect_damage(img)
        print(f"    - Train coverage: {result.get('train_coverage', 0)*100:.1f}%")
        print(f"    - Has damage: {result.get('has_damage', False)}")
        print(f"    - Damage count: {result.get('damage_count', 0)}")
        if result.get('has_damage'):
            print(f"    - Damage type: {result.get('damage_type')}")
            print(f"    - Confidence: {result.get('confidence', 0)*100:.1f}%")
    except Exception as e:
        print(f"    ✗ Error: {e}")

# Test 4: Test with real image if available
print("\n[TEST 4] Checking for real test images...")
test_image_paths = [
    Path('uploads'),
    Path('sessions'),
    Path('test_images'),
]

found_image = None
for base_path in test_image_paths:
    if base_path.exists():
        image_files = list(base_path.glob('**/*.jpg')) + list(base_path.glob('**/*.png'))
        if image_files:
            found_image = image_files[0]
            break

if found_image:
    print(f"  Found image: {found_image}")
    img = cv2.imread(str(found_image))
    if img is not None:
        print(f"  Image size: {img.shape}")
        result = detector.detect_damage(img)
        print(f"  - Train coverage: {result.get('train_coverage', 0)*100:.1f}%")
        print(f"  - Has damage: {result.get('has_damage', False)}")
        if result.get('has_damage'):
            print(f"  - Damage type: {result.get('damage_type')}")
            print(f"  - Confidence: {result.get('confidence', 0)*100:.1f}%")
            
            # Save annotated image
            output_path = Path('test_damage_output.jpg')
            cv2.imwrite(str(output_path), result['annotated_image'])
            print(f"  ✓ Saved annotated image to: {output_path}")
else:
    print("  No test images found in uploads/ or sessions/")

print("\n" + "="*70)
print("DAMAGE DETECTION TEST COMPLETE")
print("="*70)
print("\nNEXT STEPS:")
print("1. Run live processor: python live_simple_control.py")
print("2. Type 'start' to begin")
print("3. Check for damage detection messages")
print("4. Check damage_detections/ folder for saved images")
print("="*70)
