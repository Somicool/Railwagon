"""
Wagon Number OCR - Safe Extraction from Fused Images
=====================================================

Safety-critical OCR system for railway wagon inspection.
- Reads alphanumeric wagon numbers
- Validates against expected patterns
- Rejects low-confidence or unreadable results
- No hallucination or guessing
"""

import cv2
import numpy as np
import easyocr
import os
import re
from pathlib import Path


class WagonNumberOCR:
    """Safe OCR extraction for wagon numbers."""
    
    def __init__(self, confidence_threshold=0.4, languages=['en']):
        """
        Initialize OCR reader.
        
        Args:
            confidence_threshold: Minimum confidence (0.0-1.0) to accept results
            languages: Languages for OCR (default: English only)
        """
        self.confidence_threshold = confidence_threshold
        print(f"Initializing EasyOCR (languages={languages})...")
        self.reader = easyocr.Reader(languages, gpu=True)
        print("✓ OCR ready\n")
    
    def preprocess_for_ocr(self, image):
        """
        Preprocess image before OCR.
        
        Steps:
        1. Convert to grayscale
        2. Apply adaptive thresholding
        3. Remove small noise contours
        4. Keep aspect ratio unchanged
        
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
        
        # Apply adaptive thresholding for better contrast
        # Using Gaussian method to handle varying lighting
        binary = cv2.adaptiveThreshold(
            gray, 
            255, 
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            blockSize=21,
            C=10
        )
        
        # Remove small noise contours
        # Find contours
        contours, _ = cv2.findContours(
            binary.copy(), 
            cv2.RETR_EXTERNAL, 
            cv2.CHAIN_APPROX_SIMPLE
        )
        
        # Create mask to keep only larger contours
        mask = np.ones_like(binary) * 255
        min_contour_area = 20  # Minimum area to keep (pixels)
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < min_contour_area:
                cv2.drawContours(mask, [contour], -1, 0, -1)
        
        # Apply mask to remove small noise
        cleaned = cv2.bitwise_and(binary, mask)
        
        return cleaned
    
    def validate_wagon_number(self, text):
        """
        Validate if extracted text matches wagon number patterns.
        
        Expected patterns:
        - 6-11 characters total
        - Optional 2-3 letter prefix (e.g., "NF", "SW", "EC", "NR")
        - Followed by 4-9 digits
        - Examples: "NF06134", "SW123456", "EC7890123", "1234567890"
        
        Args:
            text: Extracted text string
            
        Returns:
            (is_valid, normalized_text)
        """
        # Remove all non-alphanumeric characters
        normalized = re.sub(r'[^A-Z0-9]', '', text.upper())
        
        # Check length
        if len(normalized) < 5 or len(normalized) > 12:
            return False, normalized
        
        # Pattern 1: Optional 2-3 letter prefix + 4-9 digits
        pattern1 = r'^[A-Z]{1,3}\d{4,9}$'
        
        # Pattern 2: Pure numeric (6-10 digits)
        pattern2 = r'^\d{6,10}$'
        
        if re.match(pattern1, normalized) or re.match(pattern2, normalized):
            return True, normalized
        
        return False, normalized
    
    def _filter_wagon_number_detections(self, detections):
        """
        Filter OCR detections to only keep wagon number candidates.
        Removes Hindi/Devanagari and other non-wagon-number text.
        
        Args:
            detections: List of (bbox, text, confidence) from OCR
            
        Returns:
            Filtered list of detections
        """
        filtered = []
        
        for bbox, text, confidence in detections:
            # Remove leading/trailing spaces
            text_clean = text.strip()
            
            # Check if text contains alphanumeric characters
            # Wagon numbers should have letters and/or digits
            alphanumeric_chars = sum(c.isalnum() for c in text_clean)
            total_chars = len(text_clean.replace(' ', ''))
            
            if total_chars == 0:
                continue
                
            # Keep only if majority are alphanumeric (filters Hindi/Devanagari)
            alphanumeric_ratio = alphanumeric_chars / total_chars
            
            # Also check if it looks like a wagon number pattern
            # Should contain digits and optionally letters
            has_digit = any(c.isdigit() for c in text_clean)
            has_letter = any(c.isalpha() for c in text_clean)
            
            # Wagon numbers typically have letters AND digits, or longer digit sequences
            # Filter out short numeric-only detections (likely Hindi misreads)
            is_short_numeric = (not has_letter) and (total_chars <= 3)
            
            # Accept if:
            # - High alphanumeric ratio (filters out Hindi/Devanagari)
            # - Contains digits (wagon numbers always have digits)
            # - Length is reasonable (4-15 chars for wagon number components)
            # - NOT a short numeric-only string (filters "58" type detections)
            if (alphanumeric_ratio > 0.7 and 
                has_digit and 
                4 <= total_chars <= 15 and
                not is_short_numeric):
                filtered.append((bbox, text_clean, confidence))
            # Also keep if has both letters and digits (wagon number pattern)
            elif (alphanumeric_ratio > 0.7 and
                  has_digit and has_letter):
                filtered.append((bbox, text_clean, confidence))
        
        return filtered
    
    def _create_wagon_number_image(self, wagon_number, confidence):
        """
        Create a clean image showing the detected wagon number.
        
        Args:
            wagon_number: Detected wagon number string
            confidence: Confidence score
            
        Returns:
            Image with wagon number displayed
        """
        # Create white background
        img = np.ones((150, 600, 3), dtype=np.uint8) * 255
        
        # Add wagon number (large text)
        cv2.putText(img, wagon_number, (20, 80),
                   cv2.FONT_HERSHEY_DUPLEX, 2.5, (0, 100, 0), 4)
        
        # Add confidence (small text)
        conf_text = f"Confidence: {confidence:.1%}"
        cv2.putText(img, conf_text, (20, 120),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
        
        # Add border
        cv2.rectangle(img, (5, 5), (595, 145), (0, 100, 0), 3)
        
        return img
    
    def extract_wagon_number(self, image_path, output_dir='my_fusion_results', save_visualization=True):
        """
        Extract wagon number from fused image.
        
        Args:
            image_path: Path to final_ocr_input.png
            output_dir: Directory to save results
            save_visualization: Whether to save visualization PNG
            
        Returns:
            dict with keys:
                - wagon_number: Extracted number or "UNREADABLE"
                - confidence: OCR confidence (0.0-1.0)
                - is_valid: Whether result passes validation
                - raw_detections: All OCR detections
        """
        print("=" * 70)
        print("WAGON NUMBER OCR EXTRACTION")
        print("=" * 70)
        
        # Load image
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        image = cv2.imread(image_path)
        print(f"Input: {image_path}")
        print(f"Size: {image.shape[1]}×{image.shape[0]} px\n")
        
        # Preprocess
        print("Step 1: Preprocessing for OCR")
        print("-" * 70)
        preprocessed = self.preprocess_for_ocr(image)
        print("  ✓ Grayscale conversion")
        print("  ✓ Adaptive thresholding")
        print("  ✓ Noise removal\n")
        
        # Save preprocessed image
        preprocessed_path = os.path.join(output_dir, 'ocr_preprocessed.png')
        cv2.imwrite(preprocessed_path, preprocessed)
        
        # Run OCR
        print("Step 2: Running EasyOCR")
        print("-" * 70)
        
        # EasyOCR works better on original (not preprocessed) for detection
        # But we can also try preprocessed version
        detections = self.reader.readtext(image)
        
        print(f"  Detected {len(detections)} text region(s)")
        
        # Filter to only wagon number candidates (remove Hindi/Devanagari)
        print("  Filtering wagon number candidates...")
        filtered_detections = self._filter_wagon_number_detections(detections)
        print(f"  Filtered to {len(filtered_detections)} wagon number candidate(s)\n")
        
        # Process detections
        print("Step 3: Processing Detections")
        print("-" * 70)
        
        all_texts = []
        all_confidences = []
        
        for idx, detection in enumerate(filtered_detections):
            bbox, text, confidence = detection
            print(f"  [{idx+1}] Text: '{text}' | Confidence: {confidence:.3f}")
            all_texts.append(text)
            all_confidences.append(confidence)
        
        print()
        
        # Combine all detected texts
        combined_text = ''.join(all_texts)
        avg_confidence = np.mean(all_confidences) if all_confidences else 0.0
        
        # Validate
        print("Step 4: Validation")
        print("-" * 70)
        
        is_valid, normalized_text = self.validate_wagon_number(combined_text)
        
        print(f"  Combined text: '{combined_text}'")
        print(f"  Normalized: '{normalized_text}'")
        print(f"  Average confidence: {avg_confidence:.3f}")
        print(f"  Confidence threshold: {self.confidence_threshold}")
        print(f"  Pattern valid: {is_valid}")
        
        # Decision logic
        if avg_confidence < self.confidence_threshold:
            final_result = "UNREADABLE"
            print(f"\n  ⚠ REJECTED: Confidence too low ({avg_confidence:.3f} < {self.confidence_threshold})")
        elif not is_valid:
            final_result = "UNREADABLE"
            print(f"\n  ⚠ REJECTED: Does not match wagon number pattern")
        else:
            final_result = normalized_text
            print(f"\n  ✓ ACCEPTED: '{final_result}'")
        
        print()
        
        # Create visualization
        print("Step 5: Creating Visualization")
        print("-" * 70)
        
        vis_image = image.copy()
        
        # Draw bounding boxes and text (only filtered detections)
        for detection in filtered_detections:
            bbox, text, confidence = detection
            
            # Convert bbox to integer coordinates
            pts = np.array(bbox, dtype=np.int32)
            
            # Color based on confidence
            if confidence >= self.confidence_threshold:
                color = (0, 255, 0)  # Green for good confidence
            else:
                color = (0, 0, 255)  # Red for low confidence
            
            # Draw bounding box
            cv2.polylines(vis_image, [pts], True, color, 2)
            
            # Draw text and confidence
            x, y = int(pts[0][0]), int(pts[0][1]) - 10
            label = f"{text} ({confidence:.2f})"
            cv2.putText(vis_image, label, (x, y), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        
        # Add final result at top
        result_text = f"WAGON: {final_result} (conf: {avg_confidence:.3f})"
        result_color = (0, 255, 0) if final_result != "UNREADABLE" else (0, 0, 255)
        cv2.putText(vis_image, result_text, (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 1.0, result_color, 2)
        
        if save_visualization:
            # Save visualization
            vis_path = os.path.join(output_dir, 'ocr_visualization.png')
            cv2.imwrite(vis_path, vis_image)
            print(f"  ✓ Saved: {vis_path}")
            
            # Save wagon number as clean PNG
            if final_result != "UNREADABLE":
                wagon_img = self._create_wagon_number_image(final_result, avg_confidence)
                wagon_path = os.path.join(output_dir, 'detected_wagon_number.png')
                cv2.imwrite(wagon_path, wagon_img)
                print(f"  ✓ Saved: {wagon_path}")
        
        print()
        
        # Print summary
        print("=" * 70)
        print("FINAL RESULT")
        print("=" * 70)
        print(f"\n  Wagon Number: {final_result}")
        print(f"  Confidence:   {avg_confidence:.3f}")
        print(f"  Status:       {'READABLE' if final_result != 'UNREADABLE' else 'UNREADABLE'}")
        print("\n" + "=" * 70)
        
        return {
            'wagon_number': final_result,
            'confidence': avg_confidence,
            'is_valid': is_valid and avg_confidence >= self.confidence_threshold,
            'raw_detections': detections,
            'normalized_text': normalized_text
        }


def main():
    """Main execution."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Extract wagon number from fused OCR input'
    )
    parser.add_argument(
        '--input', 
        type=str, 
        default='my_fusion_results/final_ocr_input.png',
        help='Path to final_ocr_input.png (default: my_fusion_results/final_ocr_input.png)'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default=None,
        help='Output directory (default: same as input directory)'
    )
    parser.add_argument(
        '--confidence',
        type=float,
        default=0.4,
        help='Confidence threshold (0.0-1.0, default: 0.4)'
    )
    
    args = parser.parse_args()
    
    # Determine output directory
    if args.output_dir is None:
        args.output_dir = str(Path(args.input).parent)
    
    # Create OCR system
    ocr = WagonNumberOCR(confidence_threshold=args.confidence)
    
    # Extract wagon number
    try:
        result = ocr.extract_wagon_number(args.input, args.output_dir)
        
        print("\nOutput files:")
        print(f"  - {args.output_dir}/ocr_visualization.png")
        print(f"  - {args.output_dir}/ocr_preprocessed.png")
        print()
        
        # Return exit code based on success
        if result['wagon_number'] != 'UNREADABLE':
            exit(0)  # Success
        else:
            exit(1)  # Unreadable
            
    except Exception as e:
        print("\n" + "=" * 70)
        print("ERROR")
        print("=" * 70)
        print(f"\n{e}\n")
        import traceback
        traceback.print_exc()
        print()
        exit(2)


if __name__ == '__main__':
    main()
