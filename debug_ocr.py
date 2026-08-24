"""
Debug OCR - Visualize Image and Try Multiple Approaches
========================================================

This script helps debug why OCR might not be working.
"""

import cv2
import numpy as np
import os


def debug_ocr_image(image_path):
    """Analyze image and try multiple OCR approaches."""
    
    print("=" * 70)
    print("OCR DEBUG ANALYSIS")
    print("=" * 70)
    print(f"\nImage: {image_path}\n")
    
    # Load
    img = cv2.imread(image_path)
    if img is None:
        print(f"ERROR: Could not load {image_path}")
        return
    
    print(f"Image size: {img.shape[1]} × {img.shape[0]} pixels")
    print(f"Channels: {img.shape[2] if len(img.shape) == 3 else 1}")
    
    # Convert to grayscale
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img.copy()
    
    # Calculate image statistics
    print(f"\nImage statistics:")
    print(f"  Mean brightness: {gray.mean():.1f}")
    print(f"  Min: {gray.min()}, Max: {gray.max()}")
    print(f"  Std dev: {gray.std():.1f}")
    
    # Create output directory
    debug_dir = 'ocr_debug'
    os.makedirs(debug_dir, exist_ok=True)
    
    # Try multiple preprocessing approaches
    approaches = {}
    
    # 1. Original
    approaches['1_original'] = img.copy()
    
    # 2. Grayscale
    approaches['2_grayscale'] = gray
    
    # 3. Contrast enhancement (CLAHE)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    approaches['3_clahe'] = clahe.apply(gray)
    
    # 4. Binary threshold (Otsu)
    _, binary_otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    approaches['4_binary_otsu'] = binary_otsu
    
    # 5. Adaptive threshold
    binary_adaptive = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 21, 10
    )
    approaches['5_adaptive'] = binary_adaptive
    
    # 6. Inverted adaptive
    approaches['6_adaptive_inv'] = cv2.bitwise_not(binary_adaptive)
    
    # 7. Sharpened
    kernel_sharpen = np.array([[-1,-1,-1],
                               [-1, 9,-1],
                               [-1,-1,-1]])
    sharpened = cv2.filter2D(gray, -1, kernel_sharpen)
    approaches['7_sharpened'] = sharpened
    
    # 8. Edge enhancement
    edges = cv2.Canny(gray, 50, 150)
    approaches['8_edges'] = edges
    
    # Save all approaches
    print(f"\nSaving {len(approaches)} preprocessing approaches to: {debug_dir}/")
    
    for name, processed in approaches.items():
        output_path = os.path.join(debug_dir, f'{name}.png')
        cv2.imwrite(output_path, processed)
        print(f"  ✓ {name}.png")
    
    print(f"\n{'=' * 70}")
    print("NEXT STEPS:")
    print("=" * 70)
    print(f"\n1. Check images in: {debug_dir}/")
    print("2. Find which preprocessing makes text clearest")
    print("3. If text is visible, try OCR on that specific version")
    print("4. If no text visible, the image might not contain readable text")
    print("\nTo test OCR on a specific preprocessed image:")
    print(f"  python quick_ocr_test.py {debug_dir}/5_adaptive.png")
    print()
    
    # Try to detect text regions automatically
    print("=" * 70)
    print("TEXT REGION DETECTION")
    print("=" * 70)
    
    # Use morphological operations to find text regions
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (20, 5))
    gradient = cv2.morphologyEx(gray, cv2.MORPH_GRADIENT, kernel)
    
    # Threshold
    _, thresh = cv2.threshold(gradient, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # Find contours
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Filter by size
    text_regions = []
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        area = w * h
        aspect_ratio = w / h if h > 0 else 0
        
        # Typical text region criteria
        if area > 500 and 2 < aspect_ratio < 20:
            text_regions.append((x, y, w, h))
    
    print(f"\nPotential text regions found: {len(text_regions)}")
    
    if text_regions:
        # Draw regions
        regions_vis = img.copy()
        for i, (x, y, w, h) in enumerate(text_regions):
            cv2.rectangle(regions_vis, (x, y), (x+w, y+h), (0, 255, 0), 2)
            cv2.putText(regions_vis, f"R{i+1}", (x, y-10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            print(f"  Region {i+1}: x={x}, y={y}, w={w}, h={h}")
        
        regions_path = os.path.join(debug_dir, 'detected_regions.png')
        cv2.imwrite(regions_path, regions_vis)
        print(f"\n  ✓ Saved: {regions_path}")
    else:
        print("  No clear text regions detected")
    
    print("\n" + "=" * 70)


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
    else:
        default_path = 'my_fusion_results/final_ocr_input.png'
        if os.path.exists(default_path):
            image_path = default_path
        else:
            print("Usage: python debug_ocr.py <image_path>")
            sys.exit(1)
    
    debug_ocr_image(image_path)
