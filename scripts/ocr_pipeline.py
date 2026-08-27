"""
OCR Pipeline Module
===================
Runs OCR on enhanced text regions to extract wagon numbers.

Supports:
- EasyOCR (GPU-accelerated, multilingual)
- Tesseract (CPU-based, widely used)

Includes:
- Confidence filtering
- Result visualization
- Text validation

Author: Railway Wagon Inspection System
Date: 2025-12-22
"""

import cv2
import numpy as np
from pathlib import Path
import json
from tqdm import tqdm
import re


class OCRPipeline:
    """Run OCR on enhanced text images."""
    
    def __init__(self, output_dir, ocr_engine='easyocr', 
                 min_confidence=0.3, gpu=True):
        """
        Initialize OCR pipeline.
        
        Args:
            output_dir (str): Directory to save OCR results
            ocr_engine (str): 'easyocr' or 'tesseract'
            min_confidence (float): Minimum confidence threshold (0.0-1.0)
            gpu (bool): Use GPU for EasyOCR
        """
        self.output_dir = Path(output_dir)
        self.ocr_engine = ocr_engine
        self.min_confidence = min_confidence
        self.gpu = gpu
        
        # Create output directories
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.visuals_dir = self.output_dir / "ocr_visuals"
        self.visuals_dir.mkdir(exist_ok=True)
        
        # Initialize OCR reader
        self.reader = self._init_ocr()
        
        print(f"OCR Pipeline initialized:")
        print(f"  - Engine: {ocr_engine}")
        print(f"  - Min confidence: {min_confidence}")
        print(f"  - GPU: {gpu}")
        print(f"  - Output: {self.output_dir}")
    
    def _init_ocr(self):
        """Initialize OCR engine."""
        if self.ocr_engine == 'easyocr':
            try:
                import easyocr
                reader = easyocr.Reader(['en'], gpu=self.gpu)
                print("  - EasyOCR loaded successfully")
                return reader
            except ImportError:
                print("ERROR: EasyOCR not installed. Install with: pip install easyocr")
                print("Falling back to Tesseract...")
                self.ocr_engine = 'tesseract'
        
        if self.ocr_engine == 'tesseract':
            try:
                import pytesseract
                # Test if tesseract is available
                pytesseract.get_tesseract_version()
                print("  - Tesseract loaded successfully")
                return pytesseract
            except Exception as e:
                print(f"ERROR: Tesseract not available: {e}")
                print("Install Tesseract: https://github.com/tesseract-ocr/tesseract")
                return None
    
    def run_easyocr(self, image):
        """
        Run EasyOCR on image with digit-optimized settings.
        
        Args:
            image (np.ndarray): Input image
            
        Returns:
            list: List of (text, confidence, bbox) tuples
        """
        # Use allowlist to prefer digits (0-9) and uppercase letters (A-Z)
        # This helps prevent misreading digits as similar-looking letters
        results = self.reader.readtext(
            image,
            allowlist='0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ',
            paragraph=False,  # Don't combine text blocks
            min_size=10  # Minimum text size in pixels
        )
        
        # Filter by confidence
        filtered = []
        for bbox, text, conf in results:
            if conf >= self.min_confidence:
                filtered.append((text, conf, bbox))
        
        return filtered
    
    def run_tesseract(self, image):
        """
        Run Tesseract OCR on image.
        
        Args:
            image (np.ndarray): Input image
            
        Returns:
            list: List of (text, confidence, bbox) tuples
        """
        import pytesseract
        
        # Run OCR with detailed output
        data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
        
        results = []
        n_boxes = len(data['text'])
        
        for i in range(n_boxes):
            text = data['text'][i].strip()
            conf = float(data['conf'][i]) / 100.0  # Normalize to [0, 1]
            
            if text and conf >= self.min_confidence:
                # Get bounding box
                x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
                bbox = [[x, y], [x+w, y], [x+w, y+h], [x, y+h]]
                
                results.append((text, conf, bbox))
        
        return results
    
    def process_image(self, image_path, color_image_path=None):
        """
        Run OCR on a single image.
        
        Args:
            image_path (str): Path to grayscale image for OCR
            color_image_path (str): Optional color image for visualization
            
        Returns:
            dict: OCR results
        """
        # Read image
        image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        
        if image is None:
            raise ValueError(f"Cannot read image: {image_path}")
        
        # Run OCR based on engine
        if self.ocr_engine == 'easyocr':
            results = self.run_easyocr(image)
        elif self.ocr_engine == 'tesseract':
            results = self.run_tesseract(image)
        else:
            results = []
        
        # Extract wagon numbers (heuristic: alphanumeric sequences)
        wagon_numbers = self._extract_wagon_numbers(results)
        
        # Create result dict
        result = {
            'image_path': str(image_path),
            'detections': [
                {
                    'text': text,
                    'confidence': float(conf),
                    'bbox': [[float(x), float(y)] for x, y in bbox]
                }
                for text, conf, bbox in results
            ],
            'wagon_numbers': wagon_numbers,
            'best_wagon_number': wagon_numbers[0] if wagon_numbers else None
        }
        
        # Visualize results
        if color_image_path:
            color_image = cv2.imread(color_image_path)
        else:
            color_image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        
        vis_path = self._visualize_results(color_image, results, 
                                           Path(image_path).stem)
        result['visualization'] = str(vis_path)
        
        return result
    
    def _extract_wagon_numbers(self, results):
        """
        Extract wagon numbers from OCR results using flexible heuristics.
        
        Railway wagon numbers can have multiple formats:
        - 8 digits: 12345678
        - 1 letter + 6 digits: A123456
        - Multiple letters + digits: ABC1234
        - With hyphens: 12-3456, A-123456
        - 4-12 characters total
        
        Args:
            results (list): List of OCR results
            
        Returns:
            list: Extracted wagon numbers sorted by confidence
        """
        wagon_numbers = []
        
        # First pass: try to merge nearby text that might be parts of same wagon number
        merged_results = self._merge_nearby_text(results)
        
        for text, conf, bbox in merged_results:
            # Clean text - keep letters, numbers, and hyphens
            text_clean = re.sub(r'[^A-Z0-9-]', '', text.upper())
            
            # Remove consecutive hyphens and trim
            text_clean = re.sub(r'-+', '-', text_clean).strip('-')
            
            # Check length (4-12 characters is typical for wagon numbers)
            if 4 <= len(text_clean) <= 12:
                # Extract alphanumeric portion
                alphanumeric_only = re.sub(r'[^A-Z0-9]', '', text_clean)
                
                # Check if it's a valid wagon number pattern
                if self._is_valid_wagon_number(alphanumeric_only):
                    wagon_numbers.append({
                        'number': text_clean,  # Keep hyphens in display
                        'confidence': conf,
                        'original_text': text
                    })
        
        # Remove duplicates (keep highest confidence)
        seen = {}
        for wn in wagon_numbers:
            key = wn['number']
            if key not in seen or wn['confidence'] > seen[key]['confidence']:
                seen[key] = wn
        
        wagon_numbers = list(seen.values())
        
        # Sort by confidence
        wagon_numbers.sort(key=lambda x: x['confidence'], reverse=True)
        
        return wagon_numbers
    
    def _is_valid_wagon_number(self, text):
        """
        Check if text matches valid wagon number patterns.
        
        Valid patterns:
        - 6-7 digits with 1-3 letters: A123456, AB12345, ABC123456 (alphanumeric format)
        - 8 digits ONLY: 12345678 (pure numeric, NO letters)
        
        Rules:
        - 8 digits = pure numeric (no letters/alphabets)
        - 6-7 digits = can have 1-3 letters prefix
        
        Args:
            text (str): Alphanumeric text (no hyphens/spaces)
            
        Returns:
            bool: True if valid wagon number pattern
        """
        if not text or len(text) < 7:  # Minimum: A123456 (7 chars) or 12345678 (8 chars)
            return False
        
        # Pattern 1: Exactly 8 digits = PURE NUMERIC (NO letters allowed)
        if text.isdigit():
            return len(text) == 8
        
        # Pattern 2: 6-7 digits with 1-3 letter prefix
        # Examples: A123456 (7 chars), AB123456 (8 chars), ABC1234567 (10 chars)
        # NOTE: If total length is 9+ and has letters, digits part must be 6-7 only
        letter_match = re.match(r'^([A-Z]{1,3})([0-9]{6,7})$', text)
        if letter_match:
            return True
        
        # All other patterns are INVALID
        return False

    
    def _merge_nearby_text(self, results):
        """
        Merge text detections that are close together horizontally.
        This handles cases where wagon numbers are split into multiple detections.
        
        Args:
            results (list): List of (text, conf, bbox) tuples
            
        Returns:
            list: Merged results
        """
        if not results:
            return []
        
        # Sort by x-coordinate (left to right)
        sorted_results = sorted(results, key=lambda x: min(pt[0] for pt in x[2]))
        
        merged = []
        current_group = [sorted_results[0]]
        
        for i in range(1, len(sorted_results)):
            prev_text, prev_conf, prev_bbox = current_group[-1]
            curr_text, curr_conf, curr_bbox = sorted_results[i]
            
            # Calculate horizontal distance
            prev_right = max(pt[0] for pt in prev_bbox)
            curr_left = min(pt[0] for pt in curr_bbox)
            distance = curr_left - prev_right
            
            # Calculate average character width for threshold
            prev_width = max(pt[0] for pt in prev_bbox) - min(pt[0] for pt in prev_bbox)
            avg_char_width = prev_width / max(len(prev_text), 1)
            
            # Merge if close together (within 2 character widths)
            if distance < avg_char_width * 2 and distance >= -10:  # Allow small overlap
                current_group.append(sorted_results[i])
            else:
                # Finish current group
                if len(current_group) > 1:
                    # Merge the group
                    merged_text = ''.join(t for t, _, _ in current_group)
                    merged_conf = sum(c for _, c, _ in current_group) / len(current_group)
                    merged_bbox = current_group[0][2]  # Use first bbox
                    merged.append((merged_text, merged_conf, merged_bbox))
                else:
                    merged.append(current_group[0])
                
                # Start new group
                current_group = [sorted_results[i]]
        
        # Don't forget last group
        if len(current_group) > 1:
            merged_text = ''.join(t for t, _, _ in current_group)
            merged_conf = sum(c for _, c, _ in current_group) / len(current_group)
            merged_bbox = current_group[0][2]
            merged.append((merged_text, merged_conf, merged_bbox))
        else:
            merged.append(current_group[0])
        
        return merged
    
    def _visualize_results(self, image, results, image_name):
        """
        Visualize OCR results on image.
        
        Args:
            image (np.ndarray): Color image
            results (list): OCR results
            image_name (str): Base name for output file
            
        Returns:
            str: Path to visualization
        """
        vis_image = image.copy()
        
        for text, conf, bbox in results:
            # Convert bbox to integer points
            pts = np.array(bbox, dtype=np.int32)
            
            # Draw bounding box
            cv2.polylines(vis_image, [pts], True, (0, 255, 0), 2)
            
            # Draw text with confidence
            label = f"{text} ({conf:.2f})"
            
            # Get text position (top-left of bbox)
            text_x = int(pts[0][0])
            text_y = int(pts[0][1] - 5)
            
            # Draw background rectangle for text
            (text_w, text_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(vis_image, (text_x, text_y - text_h - 2), 
                         (text_x + text_w, text_y + 2), (0, 255, 0), -1)
            
            # Draw text
            cv2.putText(vis_image, label, (text_x, text_y),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
        
        # Save visualization
        output_path = self.visuals_dir / f"{image_name}_ocr.png"
        cv2.imwrite(str(output_path), vis_image)
        
        return output_path
    
    def process_all(self, gray_paths, color_paths=None):
        """
        Process all images with OCR.
        
        Args:
            gray_paths (list): List of grayscale image paths
            color_paths (list): Optional list of color image paths for visualization
            
        Returns:
            list: List of OCR results
        """
        if color_paths is None:
            color_paths = [None] * len(gray_paths)
        
        all_results = []
        
        print(f"\nRunning OCR on {len(gray_paths)} images...")
        
        for gray_path, color_path in tqdm(zip(gray_paths, color_paths), 
                                         total=len(gray_paths),
                                         desc="OCR processing"):
            try:
                result = self.process_image(gray_path, color_path)
                all_results.append(result)
            except Exception as e:
                print(f"Error processing {gray_path}: {e}")
                continue
        
        # Save results to JSON
        results_file = self.output_dir / "ocr_results.json"
        with open(results_file, 'w') as f:
            json.dump(all_results, f, indent=2)
        
        # Save simplified text results
        text_file = self.output_dir / "ocr_results.txt"
        with open(text_file, 'w') as f:
            for i, result in enumerate(all_results):
                f.write(f"Image {i+1}: {Path(result['image_path']).name}\n")
                
                if result['best_wagon_number']:
                    wagon = result['best_wagon_number']
                    f.write(f"  Wagon Number: {wagon['number']} ")
                    f.write(f"(confidence: {wagon['confidence']:.3f})\n")
                else:
                    f.write(f"  Wagon Number: NOT DETECTED\n")
                
                f.write(f"  All detections:\n")
                for det in result['detections']:
                    f.write(f"    - {det['text']} (conf: {det['confidence']:.3f})\n")
                f.write("\n")
        
        print(f"✓ OCR complete: {len(all_results)} images processed")
        print(f"  - Results saved to: {results_file}")
        print(f"  - Text summary: {text_file}")
        print(f"  - Visualizations: {self.visuals_dir}")
        
        return all_results


def run_ocr_pipeline(enhanced_dir, output_dir="results/ocr_results",
                     ocr_engine='easyocr', min_confidence=0.3, gpu=True):
    """
    Convenience function to run OCR pipeline.
    
    Args:
        enhanced_dir (str): Directory with enhanced text images
        output_dir (str): Directory to save OCR results
        ocr_engine (str): 'easyocr' or 'tesseract'
        min_confidence (float): Minimum confidence threshold
        gpu (bool): Use GPU for EasyOCR
        
    Returns:
        list: OCR results
    """
    enhanced_dir = Path(enhanced_dir)
    
    # Get grayscale and color images
    gray_paths = sorted(enhanced_dir.glob("*_gray.png"))
    gray_paths = [str(p) for p in gray_paths]
    
    color_paths = sorted(enhanced_dir.glob("*_color.png"))
    color_paths = [str(p) for p in color_paths]
    
    if not gray_paths:
        print(f"No enhanced images found in {enhanced_dir}")
        return []
    
    # Create OCR pipeline
    ocr = OCRPipeline(output_dir, ocr_engine, min_confidence, gpu)
    return ocr.process_all(gray_paths, color_paths)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python ocr_pipeline.py <enhanced_dir> [output_dir] [engine] [min_conf]")
        print("Example: python ocr_pipeline.py results/enhanced_text results/ocr_results easyocr 0.3")
        sys.exit(1)
    
    enhanced_dir = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "results/ocr_results"
    engine = sys.argv[3] if len(sys.argv) > 3 else 'easyocr'
    min_conf = float(sys.argv[4]) if len(sys.argv) > 4 else 0.3
    
    results = run_ocr_pipeline(enhanced_dir, output_dir, engine, min_conf)
    print(f"\nProcessed {len(results)} images")
    
    # Print summary
    detected = sum(1 for r in results if r['best_wagon_number'])
    print(f"Wagon numbers detected: {detected}/{len(results)}")
