"""
Test Wagon Number Detection on User Image
Demonstrates improved pattern matching for 8-digit and alphanumeric wagon numbers.
"""

import cv2
import numpy as np
from wagon_number_enhancer import WagonNumberEnhancer
from ocr_pipeline import OCRPipeline
from pathlib import Path

# Save the uploaded image
print("Processing uploaded wagon image...")

# Initialize enhancer
enhancer = WagonNumberEnhancer(
    output_dir="test_wagon_output",
    upscale_factor=3,
    clahe_clip=4.0,
    sharpen_strength=1.5
)

# Initialize OCR
ocr = OCRPipeline(
    output_dir="test_wagon_output/ocr",
    ocr_engine='easyocr',
    min_confidence=0.2,  # Lower threshold for testing
    gpu=True
)

# Check if image exists
image_path = "uploaded_wagon.jpg"
if not Path(image_path).exists():
    print(f"Please save the wagon image as: {image_path}")
    exit()

print("\nStep 1: Enhancing wagon number region...")
enhanced, binary, debug = enhancer.enhance_wagon_number(image_path)

print(f"✓ Enhanced: {enhanced}")
print(f"✓ Binary: {binary}")
print(f"✓ Debug: {debug}")

print("\nStep 2: Running OCR on enhanced image...")
result = ocr.process_image(enhanced)

print("\n" + "="*60)
print("WAGON NUMBER DETECTION RESULTS")
print("="*60)

if result['wagon_numbers']:
    print(f"\nDetected {len(result['wagon_numbers'])} wagon number(s):")
    for i, wn in enumerate(result['wagon_numbers'], 1):
        print(f"{i}. {wn['number']} (confidence: {wn['confidence']:.3f})")
        print(f"   Original text: {wn['original_text']}")
else:
    print("\nNo wagon numbers detected")

print("\nAll OCR detections:")
for det in result['detections']:
    print(f"  - {det['text']} (conf: {det['confidence']:.3f})")

print(f"\n✓ Visualization saved: {result['visualization']}")
print("="*60)
