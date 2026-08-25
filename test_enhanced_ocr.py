"""
Test Enhanced Wagon Numbers with OCR
Quick script to compare OCR results on enhanced images.
"""

import cv2
import easyocr
from pathlib import Path
import json
from tqdm import tqdm

# Initialize EasyOCR
print("Loading EasyOCR...")
reader = easyocr.Reader(['en'], gpu=True)
print("✓ EasyOCR loaded")

# Process binary enhanced images (best for OCR)
input_dir = Path("train4_sharp_ocr")
binary_images = sorted(input_dir.glob("*_binary.png"))

print(f"\nProcessing {len(binary_images)} enhanced images...")

results = []
detections = 0

for img_path in tqdm(binary_images[:30], desc="OCR on enhanced images"):  # Test first 30
    try:
        # Read image
        img = cv2.imread(str(img_path))
        
        # Run OCR
        ocr_results = reader.readtext(img)
        
        # Filter wagon number patterns
        for (bbox, text, conf) in ocr_results:
            # Clean text
            text = text.strip().upper()
            
            # Check if it looks like a wagon number
            if len(text) >= 4 and conf > 0.3:
                results.append({
                    'file': img_path.stem,
                    'text': text,
                    'confidence': round(conf, 3)
                })
                detections += 1
                print(f"  ✓ {img_path.stem}: {text} (conf: {conf:.3f})")
                
    except Exception as e:
        print(f"  ✗ Error: {e}")
        continue

print(f"\n{'='*60}")
print(f"RESULTS SUMMARY")
print(f"{'='*60}")
print(f"Images processed: 30")
print(f"Detections: {detections}")
print(f"Detection rate: {detections/30*100:.1f}%")
print(f"{'='*60}")

# Save results
with open("enhanced_ocr_results.json", "w") as f:
    json.dump(results, f, indent=2)

print(f"\n✓ Results saved to enhanced_ocr_results.json")
