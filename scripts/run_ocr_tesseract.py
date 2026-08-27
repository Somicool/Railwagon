"""
Wagon Number OCR - Simple Tesseract Version
============================================

Lightweight OCR for wagon number extraction using Tesseract.
Alternative to EasyOCR with simpler dependencies.
"""

import cv2
import numpy as np
import os
import re
from pathlib import Path

# Try to import pytesseract
try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    print("WARNING: pytesseract not installed. Install with: pip install pytesseract")
    print("Also install Tesseract OCR: https://github.com/tesseract-ocr/tesseract")


class WagonNumberOCR_Tesseract:
    """Simple OCR extraction for wagon numbers using Tesseract."""
    
    def __init__(self, confidence_threshold=40):
        """
        Initialize OCR.
        
        Args:
            confidence_threshold: Minimum confidence (0-100) to accept results
        """
        self.confidence_threshold = confidence_threshold
        
        if not TESSERACT_AVAILABLE:
            raise ImportError("pytesseract not available. Install: pip install pytesseract")
        
        # Test Tesseract installation
        try:
            version = pytesseract.get_tesseract_version()
            print(f"Tesseract version: {version}")
            print("✓ OCR ready\n")
        except:
            print("ERROR: Tesseract not found. Please install Tesseract OCR.")
            print("Download from: https://github.com/UB-Mannheim/tesseract/wiki")
            raise
    
    def preprocess_for_ocr(self, image):
        """
        Preprocess image before OCR.
        
        Args:
            image: Input BGR image
            
        Returns:
            Preprocessed grayscale image
        """
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # Apply adaptive thresholding
        binary = cv2.adaptiveThreshold(
            gray, 
            255, 
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            blockSize=21,
            C=10
        )
        
        # Remove small noise
        kernel = np.ones((2, 2), np.uint8)
        cleaned = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
        
        return cleaned
    
    def validate_wagon_number(self, text):
        """Validate wagon number pattern."""
        # Remove all non-alphanumeric
        normalized = re.sub(r'[^A-Z0-9]', '', text.upper())
        
        # Check length
        if len(normalized) < 6 or len(normalized) > 11:
            return False, normalized
        
        # Pattern: Optional 2-letter prefix + 6-9 digits
        pattern1 = r'^[A-Z]{0,2}\d{6,9}$'
        pattern2 = r'^\d{6,10}$'
        
        if re.match(pattern1, normalized) or re.match(pattern2, normalized):
            return True, normalized
        
        return False, normalized
    
    def extract_wagon_number(self, image_path, output_dir='my_fusion_results'):
        """
        Extract wagon number from fused image.
        
        Args:
            image_path: Path to final_ocr_input.png
            output_dir: Directory to save results
            
        Returns:
            dict with extraction results
        """
        print("=" * 70)
        print("WAGON NUMBER OCR EXTRACTION (Tesseract)")
        print("=" * 70)
        
        # Load image
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        image = cv2.imread(image_path)
        print(f"Input: {image_path}")
        print(f"Size: {image.shape[1]}×{image.shape[0]} px\n")
        
        # Preprocess
        print("Step 1: Preprocessing")
        print("-" * 70)
        preprocessed = self.preprocess_for_ocr(image)
        print("  ✓ Grayscale + thresholding")
        print("  ✓ Noise removal\n")
        
        # Save preprocessed
        preprocessed_path = os.path.join(output_dir, 'ocr_preprocessed.png')
        cv2.imwrite(preprocessed_path, preprocessed)
        
        # Run OCR with detailed output
        print("Step 2: Running Tesseract OCR")
        print("-" * 70)
        
        # Configure Tesseract: alphanumeric only, English
        custom_config = r'--oem 3 --psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        
        # Get detailed data
        data = pytesseract.image_to_data(
            preprocessed,
            config=custom_config,
            output_type=pytesseract.Output.DICT
        )
        
        # Extract text and confidence
        n_boxes = len(data['text'])
        valid_texts = []
        valid_confidences = []
        vis_image = image.copy()
        
        for i in range(n_boxes):
            text = data['text'][i].strip()
            conf = int(data['conf'][i]) if data['conf'][i] != '-1' else 0
            
            if text:  # Non-empty text
                valid_texts.append(text)
                valid_confidences.append(conf)
                
                # Draw bounding box
                x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
                
                color = (0, 255, 0) if conf >= self.confidence_threshold else (0, 0, 255)
                cv2.rectangle(vis_image, (x, y), (x + w, y + h), color, 2)
                
                label = f"{text} ({conf}%)"
                cv2.putText(vis_image, label, (x, y - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                
                print(f"  Detected: '{text}' | Confidence: {conf}%")
        
        print()
        
        # Combine texts
        combined_text = ''.join(valid_texts)
        avg_confidence = np.mean(valid_confidences) if valid_confidences else 0.0
        
        print("Step 3: Validation")
        print("-" * 70)
        print(f"  Combined: '{combined_text}'")
        
        is_valid, normalized = self.validate_wagon_number(combined_text)
        
        print(f"  Normalized: '{normalized}'")
        print(f"  Avg confidence: {avg_confidence:.1f}%")
        print(f"  Threshold: {self.confidence_threshold}%")
        print(f"  Pattern valid: {is_valid}")
        
        # Decision
        if avg_confidence < self.confidence_threshold:
            final_result = "UNREADABLE"
            print(f"\n  ⚠ REJECTED: Low confidence ({avg_confidence:.1f}% < {self.confidence_threshold}%)")
        elif not is_valid:
            final_result = "UNREADABLE"
            print(f"\n  ⚠ REJECTED: Invalid pattern")
        else:
            final_result = normalized
            print(f"\n  ✓ ACCEPTED: '{final_result}'")
        
        print()
        
        # Add result to visualization
        result_text = f"RESULT: {final_result} ({avg_confidence:.1f}%)"
        result_color = (0, 255, 0) if final_result != "UNREADABLE" else (0, 0, 255)
        cv2.putText(vis_image, result_text, (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 1.0, result_color, 2)
        
        # Save visualization
        vis_path = os.path.join(output_dir, 'ocr_visualization.png')
        cv2.imwrite(vis_path, vis_image)
        print(f"  ✓ Saved: {vis_path}\n")
        
        # Summary
        print("=" * 70)
        print("FINAL RESULT")
        print("=" * 70)
        print(f"\n  Wagon Number: {final_result}")
        print(f"  Confidence:   {avg_confidence:.1f}%")
        print(f"  Status:       {'READABLE' if final_result != 'UNREADABLE' else 'UNREADABLE'}")
        print("\n" + "=" * 70)
        
        return {
            'wagon_number': final_result,
            'confidence': avg_confidence / 100.0,  # Normalize to 0-1
            'is_valid': is_valid and avg_confidence >= self.confidence_threshold,
            'raw_text': combined_text,
            'normalized_text': normalized
        }


def main():
    """Main execution."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Extract wagon number using Tesseract OCR'
    )
    parser.add_argument(
        '--input',
        type=str,
        default='my_fusion_results/final_ocr_input.png',
        help='Path to input image'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default=None,
        help='Output directory'
    )
    parser.add_argument(
        '--confidence',
        type=int,
        default=40,
        help='Confidence threshold (0-100, default: 40)'
    )
    
    args = parser.parse_args()
    
    if args.output_dir is None:
        args.output_dir = str(Path(args.input).parent)
    
    try:
        ocr = WagonNumberOCR_Tesseract(confidence_threshold=args.confidence)
        result = ocr.extract_wagon_number(args.input, args.output_dir)
        
        print("\nOutput files:")
        print(f"  - {args.output_dir}/ocr_visualization.png")
        print(f"  - {args.output_dir}/ocr_preprocessed.png")
        print()
        
        exit(0 if result['wagon_number'] != 'UNREADABLE' else 1)
        
    except Exception as e:
        print("\n" + "=" * 70)
        print("ERROR")
        print("=" * 70)
        print(f"\n{e}\n")
        import traceback
        traceback.print_exc()
        exit(2)


if __name__ == '__main__':
    main()
