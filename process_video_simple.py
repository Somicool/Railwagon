"""
Simple Railway Video Processor - Without Deblurring
Extracts 1 frame per second, enhances for motion blur, and detects wagon numbers using OCR.
Saves annotated images with detected wagon numbers highlighted.
"""

import cv2
import numpy as np
from pathlib import Path
import json
import re
import sys


class RailwayVideoProcessor:
    """Process railway video: extract frames and detect wagon numbers."""
    
    def __init__(self):
        """Initialize processor."""
        # Try to import EasyOCR
        self.ocr_reader = None
        try:
            import easyocr
            print("Loading EasyOCR (this may take a moment)...")
            self.ocr_reader = easyocr.Reader(['en'], gpu=True)
            print("EasyOCR loaded successfully!")
        except Exception as e:
            print(f"Warning: Could not load EasyOCR: {e}")
            print("OCR detection will be skipped.")
    
    def extract_frames(self, video_path, output_dir, fps=1):
        """Extract frames from video at specified FPS."""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Open video
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise ValueError(f"Could not open video: {video_path}")
        
        # Get video properties
        video_fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        print(f"\nVideo Info:")
        print(f"  Resolution: {width}x{height}")
        print(f"  FPS: {video_fps:.2f}")
        print(f"  Total frames: {total_frames}")
        print(f"  Duration: {total_frames/video_fps:.2f} seconds")
        print(f"  Extracting at: {fps} frame(s) per second")
        
        # Calculate frame interval
        frame_interval = int(video_fps / fps)
        
        # Extract frames
        frame_count = 0
        saved_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Save frame at intervals (full color, normal size)
            if frame_count % frame_interval == 0:
                frame_path = output_dir / f"frame_{saved_count:04d}.jpg"
                cv2.imwrite(str(frame_path), frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
                saved_count += 1
                
                if saved_count % 5 == 0:
                    print(f"  Extracted {saved_count} frames...", end='\r')
            
            frame_count += 1
        
        cap.release()
        print(f"\nExtracted {saved_count} full color frames to {output_dir}")
        return saved_count
    
    def enhance_frame(self, image):
        """Enhance frame for better OCR (handles motion blur)."""
        # Convert to LAB color space for better enhancement
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        
        # Merge back
        enhanced_lab = cv2.merge([l, a, b])
        enhanced = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)
        
        # Apply sharpening to reduce blur effect
        kernel = np.array([[-1, -1, -1],
                          [-1,  9, -1],
                          [-1, -1, -1]])
        sharpened = cv2.filter2D(enhanced, -1, kernel)
        
        # Blend original and sharpened (70% sharpened, 30% original)
        result = cv2.addWeighted(sharpened, 0.7, enhanced, 0.3, 0)
        
        return result
    
    def detect_wagon_numbers(self, images_dir, output_file, annotated_dir=None):
        """Detect wagon numbers using OCR and save annotated images."""
        if self.ocr_reader is None:
            print("\nOCR not available - skipping wagon number detection")
            print("Frames are saved and ready for manual inspection.")
            return
        
        images_dir = Path(images_dir)
        image_files = sorted(images_dir.glob("*.jpg"))
        
        # Create annotated output directory
        if annotated_dir is None:
            annotated_dir = Path(output_file).parent / "detected_wagon_numbers"
        else:
            annotated_dir = Path(annotated_dir)
        annotated_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"\nDetecting wagon numbers in {len(image_files)} frames...")
        print(f"Annotated images will be saved to: {annotated_dir}")
        
        results = []
        summary = []
        
        for i, img_path in enumerate(image_files):
            # Read image
            img = cv2.imread(str(img_path))
            
            # Enhance image for better OCR (especially for motion blur)
            enhanced_img = self.enhance_frame(img)
            
            # Create a copy for annotation
            annotated_img = img.copy()
            
            # Run OCR on enhanced image
            try:
                ocr_results = self.ocr_reader.readtext(enhanced_img)
                
                # Extract potential wagon numbers (4-12 alphanumeric characters)
                wagon_numbers = []
                for bbox, text, confidence in ocr_results:
                    # Clean text
                    text_clean = re.sub(r'[^A-Z0-9]', '', text.upper())
                    
                    # Check if it looks like a wagon number
                    if 4 <= len(text_clean) <= 12 and confidence > 0.4:
                        wagon_numbers.append({
                            'text': text_clean,
                            'confidence': float(confidence),
                            'original': text,
                            'bbox': [[float(x), float(y)] for x, y in bbox]
                        })
                        
                        # Draw bounding box on annotated image
                        pts = np.array(bbox, dtype=np.int32).reshape((-1, 1, 2))
                        cv2.polylines(annotated_img, [pts], True, (0, 255, 0), 3)
                        
                        # Add text label with confidence
                        top_left = tuple(pts[0][0])
                        label = f"{text_clean} ({confidence:.2f})"
                        
                        # Draw background for text
                        (text_width, text_height), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)
                        cv2.rectangle(annotated_img, 
                                    (top_left[0], top_left[1] - text_height - 10),
                                    (top_left[0] + text_width, top_left[1]),
                                    (0, 255, 0), -1)
                        
                        # Draw text
                        cv2.putText(annotated_img, label,
                                  (top_left[0], top_left[1] - 5),
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
                
                if wagon_numbers:
                    # Sort by confidence
                    wagon_numbers.sort(key=lambda x: x['confidence'], reverse=True)
                    
                    results.append({
                        'frame': img_path.name,
                        'frame_number': i,
                        'wagon_numbers': wagon_numbers,
                        'best_detection': wagon_numbers[0]['text']
                    })
                    
                    summary.append(f"Frame {i:03d}: {wagon_numbers[0]['text']} (confidence: {wagon_numbers[0]['confidence']:.2f})")
                    print(f"  Frame {i+1}/{len(image_files)}: Found {len(wagon_numbers)} candidate(s) - Best: {wagon_numbers[0]['text']}")
                    
                    # Save annotated image
                    annotated_path = annotated_dir / f"detected_{img_path.name}"
                    cv2.imwrite(str(annotated_path), annotated_img, [cv2.IMWRITE_JPEG_QUALITY, 95])
                else:
                    print(f"  Frame {i+1}/{len(image_files)}: No wagon numbers detected")
            
            except Exception as e:
                print(f"  Frame {i+1}/{len(image_files)}: OCR error - {e}")
        
        # Save results
        output_data = {
            'summary': {
                'total_frames': len(image_files),
                'frames_with_detections': len(results),
                'detection_rate': len(results) / len(image_files) if image_files else 0
            },
            'detections': results
        }
        
        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        # Save summary text file
        summary_file = Path(output_file).parent / "detection_summary.txt"
        with open(summary_file, 'w') as f:
            f.write("Wagon Number Detection Summary\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Total frames processed: {len(image_files)}\n")
            f.write(f"Frames with detections: {len(results)}\n")
            f.write(f"Detection rate: {len(results) / len(image_files) * 100:.1f}%\n\n")
            f.write("Detections:\n")
            f.write("-" * 60 + "\n")
            for line in summary:
                f.write(line + "\n")
        
        print(f"\nDetection complete!")
        print(f"  Results saved to: {output_file}")
        print(f"  Summary saved to: {summary_file}")
        print(f"  Annotated images saved to: {annotated_dir}")
        print(f"  Found wagon numbers in {len(results)}/{len(image_files)} frames ({len(results)/len(image_files)*100:.1f}%)")
        print(f"  Saved {len(results)} annotated images with detected wagon numbers")


def main():
    """Main processing pipeline."""
    if len(sys.argv) < 2:
        print("Usage: python process_video_simple.py <video_path> [output_dir]")
        print("Example: python process_video_simple.py 'railway vid 3.mp4' output")
        return
    
    video_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "railway_output"
    
    # Verify inputs
    if not Path(video_path).exists():
        print(f"Error: Video file not found: {video_path}")
        return
    
    print("=" * 60)
    print("Railway Video Processor")
    print("Full Color Frames | 1 FPS | Motion Blur Enhanced OCR")
    print("=" * 60)
    
    # Create output directory structure
    base_output = Path(output_dir)
    frames_dir = base_output / "frames"
    results_file = base_output / "wagon_numbers.json"
    
    # Initialize processor
    processor = RailwayVideoProcessor()
    
    # Step 1: Extract frames
    print("\n" + "=" * 60)
    print("STEP 1: Extracting Frames (1 FPS, Full Color)")
    print("=" * 60)
    num_frames = processor.extract_frames(video_path, frames_dir, fps=1)
    
    # Step 2: Detect wagon numbers
    print("\n" + "=" * 60)
    print("STEP 2: Detecting Wagon Numbers (with Motion Blur Enhancement)")
    print("=" * 60)
    processor.detect_wagon_numbers(frames_dir, results_file)
    
    # Summary
    print("\n" + "=" * 60)
    print("PROCESSING COMPLETE!")
    print("=" * 60)
    print(f"\nOutput directory: {base_output}")
    print(f"  - Frames (full color, normal size): {frames_dir}")
    if processor.ocr_reader:
        print(f"  - Detected wagon numbers (annotated images): {base_output / 'detected_wagon_numbers'}")
        print(f"  - Detection results (JSON): {results_file}")
        print(f"  - Detection summary (TXT): {base_output / 'detection_summary.txt'}")
    print("\nYou can now:")
    print(f"  1. View frames in: {frames_dir}")
    if processor.ocr_reader:
        print(f"  2. View detected wagon numbers (images): {base_output / 'detected_wagon_numbers'}")
        print(f"  3. Check detection summary: detection_summary.txt")
        print(f"  4. See detailed results: wagon_numbers.json")
    print("=" * 60)


if __name__ == "__main__":
    main()
