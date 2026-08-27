"""
Simplified Railway Video Processor
===================================
Process railway video with:
- 1 frame per second extraction
- Full color images (no cropping)
- Deblurring on each frame
- OCR on full frames
- Wagon number detection
"""

import cv2
import torch
import numpy as np
from pathlib import Path
from tqdm import tqdm
import re
import json

# Import model
from models.mimo_unet_plus import MIMOUNetPlus


class RailwayVideoProcessor:
    """Process railway video and detect wagon numbers."""
    
    def __init__(self, video_path, model_path, output_dir="railway_results"):
        self.video_path = video_path
        self.model_path = model_path
        self.output_dir = Path(output_dir)
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Create output directories
        self.frames_dir = self.output_dir / "1_frames"
        self.deblurred_dir = self.output_dir / "2_deblurred"
        self.results_dir = self.output_dir / "3_results"
        
        for d in [self.frames_dir, self.deblurred_dir, self.results_dir]:
            d.mkdir(parents=True, exist_ok=True)
        
        print("="*70)
        print("RAILWAY VIDEO PROCESSOR")
        print("="*70)
        print(f"Video: {video_path}")
        print(f"Output: {output_dir}")
        print(f"Device: {self.device}")
        print("="*70)
        
        # Load deblurring model
        self._load_model()
        
        # Initialize OCR
        self._init_ocr()
    
    def _load_model(self):
        """Load deblurring model."""
        print(f"\nLoading deblurring model from: {self.model_path}")
        self.model = MIMOUNetPlus().to(self.device)
        checkpoint = torch.load(self.model_path, map_location=self.device, weights_only=False)
        
        if isinstance(checkpoint, dict) and 'model_state_dict' in checkpoint:
            self.model.load_state_dict(checkpoint['model_state_dict'])
            if 'best_psnr' in checkpoint:
                print(f"  Fine-tuned model - Best PSNR: {checkpoint['best_psnr']:.2f} dB")
        else:
            self.model.load_state_dict(checkpoint)
        
        self.model.eval()
        print("✓ Model loaded successfully")
    
    def _init_ocr(self):
        """Initialize OCR engine."""
        print("\nInitializing OCR...")
        try:
            import pytesseract
            pytesseract.get_tesseract_version()
            self.ocr_engine = 'tesseract'
            self.ocr = pytesseract
            print("✓ Tesseract OCR ready")
        except:
            print("⚠ Tesseract not found - OCR will be skipped")
            print("  Install from: https://github.com/UB-Mannheim/tesseract/wiki")
            self.ocr_engine = None
    
    def extract_frames(self, fps=1):
        """Extract frames at specified FPS."""
        print(f"\nStep 1: Extracting frames at {fps} FPS...")
        
        cap = cv2.VideoCapture(self.video_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {self.video_path}")
        
        video_fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / video_fps if video_fps > 0 else 0
        
        print(f"Video: {video_fps:.1f} FPS, {total_frames} frames, {duration:.1f}s")
        
        # Calculate frame interval
        frame_interval = int(video_fps / fps) if fps < video_fps else 1
        
        frame_count = 0
        saved_count = 0
        frame_paths = []
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            if frame_count % frame_interval == 0:
                filename = f"frame_{saved_count:04d}.png"
                output_path = self.frames_dir / filename
                cv2.imwrite(str(output_path), frame)
                frame_paths.append(str(output_path))
                saved_count += 1
            
            frame_count += 1
        
        cap.release()
        print(f"✓ Extracted {saved_count} frames -> {self.frames_dir}")
        return frame_paths
    
    def deblur_frame(self, image):
        """Apply deblurring to a single frame."""
        # Get original dimensions
        h, w = image.shape[:2]
        
        # Pad to multiple of 8
        new_h = ((h + 7) // 8) * 8
        new_w = ((w + 7) // 8) * 8
        
        padded = cv2.copyMakeBorder(image, 0, new_h - h, 0, new_w - w, 
                                    cv2.BORDER_REFLECT)
        
        # Convert to tensor
        img_tensor = torch.from_numpy(padded).float().permute(2, 0, 1).unsqueeze(0) / 255.0
        img_tensor = img_tensor.to(self.device)
        
        # Run model
        with torch.no_grad():
            outputs = self.model(img_tensor)
            output = outputs[-1] if isinstance(outputs, (list, tuple)) else outputs
        
        # Convert back to image
        output_img = output.squeeze(0).permute(1, 2, 0).cpu().numpy()
        output_img = np.clip(output_img * 255.0, 0, 255).astype(np.uint8)
        output_img = output_img[:h, :w]  # Remove padding
        
        return output_img
    
    def deblur_all_frames(self, frame_paths):
        """Deblur all extracted frames."""
        print(f"\nStep 2: Deblurring {len(frame_paths)} frames...")
        
        deblurred_paths = []
        
        for frame_path in tqdm(frame_paths, desc="Deblurring"):
            # Read frame
            frame = cv2.imread(frame_path)
            
            # Deblur
            deblurred = self.deblur_frame(frame)
            
            # Save
            filename = Path(frame_path).name
            output_path = self.deblurred_dir / filename
            cv2.imwrite(str(output_path), deblurred)
            deblurred_paths.append(str(output_path))
        
        print(f"✓ Deblurred {len(deblurred_paths)} frames -> {self.deblurred_dir}")
        return deblurred_paths
    
    def detect_wagon_number(self, image_path):
        """Detect wagon number from image using OCR."""
        if self.ocr_engine is None:
            return None
        
        # Read image
        img = cv2.imread(image_path)
        
        # Run OCR
        text = self.ocr.image_to_string(img, config='--psm 6')
        
        # Extract potential wagon numbers
        wagon_numbers = []
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        for line in lines:
            # Clean text
            clean = re.sub(r'[^A-Z0-9-]', '', line.upper())
            
            # Check if it looks like a wagon number (4-12 chars, has letters or numbers)
            if 4 <= len(clean) <= 12:
                has_letter = bool(re.search(r'[A-Z]', clean))
                has_number = bool(re.search(r'[0-9]', clean))
                
                if has_letter or has_number:
                    wagon_numbers.append(clean)
        
        return {
            'image': Path(image_path).name,
            'raw_text': text,
            'wagon_numbers': wagon_numbers,
            'best_match': wagon_numbers[0] if wagon_numbers else None
        }
    
    def run_ocr_on_all(self, deblurred_paths):
        """Run OCR on all deblurred frames."""
        print(f"\nStep 3: Running OCR on {len(deblurred_paths)} frames...")
        
        if self.ocr_engine is None:
            print("⚠ OCR skipped - Tesseract not installed")
            return []
        
        results = []
        wagon_numbers_found = []
        
        for img_path in tqdm(deblurred_paths, desc="OCR processing"):
            result = self.detect_wagon_number(img_path)
            results.append(result)
            
            if result['best_match']:
                wagon_numbers_found.append(result['best_match'])
        
        # Save results
        results_file = self.results_dir / "ocr_results.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        # Save text summary
        summary_file = self.results_dir / "wagon_numbers.txt"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("="*70 + "\n")
            f.write("WAGON NUMBER DETECTION RESULTS\n")
            f.write("="*70 + "\n\n")
            
            f.write(f"Total frames processed: {len(results)}\n")
            f.write(f"Frames with wagon numbers: {len(wagon_numbers_found)}\n")
            f.write(f"Unique wagon numbers: {len(set(wagon_numbers_found))}\n\n")
            
            if wagon_numbers_found:
                from collections import Counter
                f.write("DETECTED WAGON NUMBERS (by frequency):\n")
                f.write("-"*70 + "\n")
                for num, count in Counter(wagon_numbers_found).most_common():
                    f.write(f"{num}: {count} frames\n")
                f.write("\n")
            
            f.write("="*70 + "\n")
            f.write("FRAME-BY-FRAME RESULTS\n")
            f.write("="*70 + "\n\n")
            
            for r in results:
                f.write(f"Frame: {r['image']}\n")
                if r['best_match']:
                    f.write(f"Wagon Number: {r['best_match']}\n")
                else:
                    f.write("Wagon Number: NOT DETECTED\n")
                if r['wagon_numbers']:
                    f.write(f"All detected: {', '.join(r['wagon_numbers'])}\n")
                f.write("\n")
        
        print(f"✓ OCR complete")
        print(f"  - Results: {results_file}")
        print(f"  - Summary: {summary_file}")
        
        return results
    
    def process(self):
        """Run complete processing pipeline."""
        # Extract frames at 1 FPS
        frame_paths = self.extract_frames(fps=1)
        
        # Deblur all frames
        deblurred_paths = self.deblur_all_frames(frame_paths)
        
        # Run OCR
        ocr_results = self.run_ocr_on_all(deblurred_paths)
        
        # Print summary
        print("\n" + "="*70)
        print("PROCESSING COMPLETE")
        print("="*70)
        print(f"Frames extracted: {len(frame_paths)}")
        print(f"Frames deblurred: {len(deblurred_paths)}")
        
        if ocr_results:
            detected = sum(1 for r in ocr_results if r['best_match'])
            print(f"Wagon numbers detected: {detected}/{len(ocr_results)}")
            
            if detected > 0:
                from collections import Counter
                all_nums = [r['best_match'] for r in ocr_results if r['best_match']]
                print("\nMOST COMMON WAGON NUMBERS:")
                for num, count in Counter(all_nums).most_common(5):
                    print(f"  {num}: {count} times")
        
        print(f"\nAll results in: {self.output_dir}")
        print("="*70)
        
        return {
            'frames': frame_paths,
            'deblurred': deblurred_paths,
            'ocr_results': ocr_results
        }


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("\nUsage: python process_railway_video.py <video_path> <model_path> [output_dir]")
        print("\nExample:")
        print('  python process_railway_video.py "railway vid 3.mp4" weights/gopro_best.pth')
        print('  python process_railway_video.py "railway vid 3.mp4" weights/gopro_best.pth my_results')
        sys.exit(1)
    
    video_path = sys.argv[1]
    model_path = sys.argv[2]
    output_dir = sys.argv[3] if len(sys.argv) > 3 else "railway_results"
    
    processor = RailwayVideoProcessor(video_path, model_path, output_dir)
    processor.process()
