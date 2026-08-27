"""
Quick OCR Test - Simple Single-Image Test
==========================================

Simplest way to test OCR on any image.
"""

import cv2
import numpy as np
import re
import os

def simple_ocr_test(image_path):
    """
    Test OCR on a single image using either EasyOCR or Tesseract.
    Automatically detects which is available.
    """
    
    print("=" * 70)
    print("SIMPLE OCR TEST")
    print("=" * 70)
    print(f"\nImage: {image_path}\n")
    
    # Check availability
    easyocr_available = False
    tesseract_available = False
    
    try:
        import easyocr
        easyocr_available = True
        print("✓ EasyOCR available")
    except:
        print("✗ EasyOCR not available")
    
    try:
        import pytesseract
        pytesseract.get_tesseract_version()
        tesseract_available = True
        print("✓ Tesseract available")
    except:
        print("✗ Tesseract not available")
    
    print()
    
    if not easyocr_available and not tesseract_available:
        print("ERROR: No OCR engine available!")
        print("\nInstall one of:")
        print("  1. EasyOCR: pip install easyocr")
        print("  2. Tesseract: pip install pytesseract + download binary")
        return
    
    # Load image
    img = cv2.imread(image_path)
    if img is None:
        print(f"ERROR: Could not load image: {image_path}")
        return
    
    # Preprocess
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
    
    # Try EasyOCR first (usually better)
    if easyocr_available:
        print("Using: EasyOCR")
        print("-" * 70)
        print("Initializing...")
        
        reader = easyocr.Reader(['en'], gpu=False)  # CPU mode for compatibility
        print("Running OCR...")
        
        results = reader.readtext(img)
        
        print(f"\nDetected {len(results)} text region(s):\n")
        
        for i, (bbox, text, conf) in enumerate(results):
            print(f"  [{i+1}] '{text}' (confidence: {conf:.3f})")
        
        # Combine
        combined = ''.join([text for _, text, _ in results])
        avg_conf = np.mean([conf for _, _, conf in results]) if results else 0.0
        
        print(f"\nCombined: '{combined}'")
        print(f"Average confidence: {avg_conf:.3f}")
        
    elif tesseract_available:
        print("Using: Tesseract")
        print("-" * 70)
        
        # Preprocess for better Tesseract results
        binary = cv2.adaptiveThreshold(
            gray, 255, 
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 21, 10
        )
        
        # Config for alphanumeric only
        config = r'--oem 3 --psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        
        print("Running OCR...")
        
        data = pytesseract.image_to_data(binary, config=config, output_type=pytesseract.Output.DICT)
        
        texts = []
        confidences = []
        
        for i in range(len(data['text'])):
            text = data['text'][i].strip()
            conf = int(data['conf'][i]) if data['conf'][i] != '-1' else 0
            
            if text:
                texts.append(text)
                confidences.append(conf)
                print(f"  '{text}' (confidence: {conf}%)")
        
        combined = ''.join(texts)
        avg_conf = np.mean(confidences) if confidences else 0.0
        
        print(f"\nCombined: '{combined}'")
        print(f"Average confidence: {avg_conf:.1f}%")
    
    # Validate pattern
    normalized = re.sub(r'[^A-Z0-9]', '', combined.upper())
    print(f"Normalized: '{normalized}'")
    
    # Check if looks like wagon number
    is_wagon = bool(re.match(r'^[A-Z]{0,2}\d{6,9}$', normalized) or 
                    re.match(r'^\d{6,10}$', normalized))
    
    print(f"\nLooks like wagon number: {'YES ✓' if is_wagon else 'NO ✗'}")
    
    print("\n" + "=" * 70)


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
    else:
        # Default to fusion result if available
        default_path = 'my_fusion_results/final_ocr_input.png'
        
        if os.path.exists(default_path):
            image_path = default_path
            print(f"Using default: {default_path}\n")
        else:
            print("Usage: python quick_ocr_test.py <image_path>")
            print("\nOr run temporal fusion first to create my_fusion_results/final_ocr_input.png")
            sys.exit(1)
    
    simple_ocr_test(image_path)
