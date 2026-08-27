"""
Quick Tesseract OCR for Railway Video Results
"""
import cv2
import os
from pathlib import Path
import re

# Check for Tesseract
try:
    import pytesseract
    # Try to run Tesseract
    pytesseract.get_tesseract_version()
    print("✓ Tesseract found")
except:
    print("ERROR: Tesseract not installed.")
    print("Download from: https://github.com/UB-Mannheim/tesseract/wiki")
    print("Or install via: choco install tesseract")
    exit(1)

# Process the enhanced images
input_dir = Path("railway_vid3_results/4_enhanced_text")
output_file = Path("railway_vid3_results/ocr_results_tesseract.txt")

gray_images = sorted(input_dir.glob("*_gray.png"))

print(f"\nProcessing {len(gray_images)} images with Tesseract OCR...")
print(f"Output will be saved to: {output_file}\n")

results = []
wagon_numbers_found = []

for i, img_path in enumerate(gray_images, 1):
    # Read image
    img = cv2.imread(str(img_path))
    
    # Run OCR
    text = pytesseract.image_to_string(img, config='--psm 6')
    
    # Clean and extract potential wagon numbers
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    # Look for alphanumeric sequences (wagon numbers)
    wagon_nums = []
    for line in lines:
        # Remove spaces and special chars
        clean = re.sub(r'[^A-Z0-9-]', '', line.upper())
        # Keep if 4-12 characters with letters or numbers
        if 4 <= len(clean) <= 12:
            has_letter = bool(re.search(r'[A-Z]', clean))
            has_number = bool(re.search(r'[0-9]', clean))
            if has_letter or has_number:
                wagon_nums.append(clean)
    
    results.append({
        'image': img_path.name,
        'text': text,
        'wagon_numbers': wagon_nums
    })
    
    if wagon_nums:
        wagon_numbers_found.extend(wagon_nums)
        print(f"✓ Frame {i:3d}: Found {wagon_nums}")
    else:
        print(f"  Frame {i:3d}: No wagon numbers detected", end='\r')

# Save results
with open(output_file, 'w', encoding='utf-8') as f:
    f.write("="*70 + "\n")
    f.write("RAILWAY VIDEO OCR RESULTS (Tesseract)\n")
    f.write("="*70 + "\n\n")
    
    f.write(f"Total frames processed: {len(gray_images)}\n")
    f.write(f"Wagon numbers detected: {len(set(wagon_numbers_found))}\n\n")
    
    if wagon_numbers_found:
        f.write("UNIQUE WAGON NUMBERS FOUND:\n")
        f.write("-"*70 + "\n")
        for num in sorted(set(wagon_numbers_found)):
            count = wagon_numbers_found.count(num)
            f.write(f"{num} (appeared in {count} frames)\n")
        f.write("\n")
    
    f.write("="*70 + "\n")
    f.write("DETAILED RESULTS PER FRAME\n")
    f.write("="*70 + "\n\n")
    
    for r in results:
        f.write(f"Image: {r['image']}\n")
        if r['wagon_numbers']:
            f.write(f"Wagon Numbers: {', '.join(r['wagon_numbers'])}\n")
        else:
            f.write("Wagon Numbers: NOT DETECTED\n")
        f.write(f"Raw Text:\n{r['text']}\n")
        f.write("-"*70 + "\n\n")

print(f"\n\n{'='*70}")
print("SUMMARY")
print("="*70)
print(f"Total frames: {len(gray_images)}")
print(f"Unique wagon numbers: {len(set(wagon_numbers_found))}")

if wagon_numbers_found:
    print("\nMOST COMMON WAGON NUMBERS:")
    from collections import Counter
    for num, count in Counter(wagon_numbers_found).most_common(10):
        print(f"  {num}: {count} frames")

print(f"\nFull results saved to: {output_file}")
print("="*70)
