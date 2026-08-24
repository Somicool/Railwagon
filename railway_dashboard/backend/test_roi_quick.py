"""Quick test of ROI inspection pipeline."""

from roi_inspection_pipeline import ROIInspectionPipeline
import cv2
import os

print("\n" + "="*70)
print("ROI INSPECTION PIPELINE - QUICK TEST")
print("="*70 + "\n")

# Initialize pipeline
print("Initializing pipeline...")
pipeline = ROIInspectionPipeline(
    yolo_model_path='models/wagon_detector.pt',
    output_base_dir='test_records',
    use_global_enhancement=False,
    device='cpu'
)

# Find a test image
test_image_path = r"..\..\GOPRO_Large\train\GOPR0372_07_00\blur\000040.png"

if not os.path.exists(test_image_path):
    print(f"[WARNING] Test image not found: {test_image_path}")
    print("[INFO] Using mock test - creating synthetic frame")
    import numpy as np
    frame = np.random.randint(0, 255, (720, 1280, 3), dtype=np.uint8)
else:
    print(f"Loading test image: {test_image_path}")
    frame = cv2.imread(test_image_path)

if frame is None:
    print("[ERROR] Could not load image, creating synthetic frame")
    import numpy as np
    frame = np.random.randint(0, 255, (720, 1280, 3), dtype=np.uint8)

print(f"Image shape: {frame.shape}")
print("\nProcessing frame...\n")

# Process single frame
results = pipeline.process_frame(frame, 'quick_test_001')

# Display results
print("\n" + "="*70)
print("TEST RESULTS")
print("="*70)
print(f"ROI Detections: {results['roi_detections']}")
print(f"Wagon Numbers Found: {len(results['wagon_numbers'])}")
print(f"Damage Detections: {len(results['damage_detections'])}")

if results['wagon_numbers']:
    print("\n📋 WAGON NUMBERS:")
    for i, wn in enumerate(results['wagon_numbers'], 1):
        print(f"  {i}. Text: '{wn['text']}' | Confidence: {wn['confidence']:.2f}")

if results['damage_detections']:
    print("\n⚠️  DAMAGE DETECTIONS:")
    for i, dmg in enumerate(results['damage_detections'], 1):
        print(f"  {i}. Type: {dmg['damage_type']} | "
              f"ROI: {dmg['roi_class']} | "
              f"Confidence: {dmg['confidence']:.2f}")

print("\n" + "="*70)
print("✅ TEST COMPLETE!")
print("="*70 + "\n")
