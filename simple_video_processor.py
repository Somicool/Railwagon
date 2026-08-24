"""
Simple Railway Video Processor
Extracts 1 frame per second, deblurs, and detects wagon numbers.
"""

import cv2
import numpy as np
import torch
import torch.nn as nn
from pathlib import Path
import json
import re
import sys

# Import the deblurring model
from models.mimo_unet_plus import MIMOUNetPlus


class SimpleVideoProcessor:
    """Process railway video: extract frames, deblur, detect wagon numbers."""
    
    def __init__(self, model_path, device='cuda' if torch.cuda.is_available() else 'cpu'):
        """Initialize processor with model."""
        self.device = device
        print(f"Using device: {self.device}")
        
        # Load deblurring model
        print("Loading deblurring model...")
        self.model = self._load_model(model_path)
        print("Model loaded successfully!")
        
        # Try to import EasyOCR
        self.ocr_reader = None
        try:
            import easyocr
            print("Loading EasyOCR (this may take a moment)...")
            self.ocr_reader = easyocr.Reader(['en'], gpu=torch.cuda.is_available())
            print("EasyOCR loaded successfully!")
        except Exception as e:
            print(f"Warning: Could not load EasyOCR: {e}")
            print("OCR detection will be skipped. Install EasyOCR or Tesseract to enable OCR.")
    
    def _load_model(self, model_path):
        """Load MIMO-UNet+ deblurring model."""
        model = MIMOUNetPlus()
        
        # Load checkpoint
        checkpoint = torch.load(model_path, map_location=self.device)
        
        # Handle different checkpoint formats
        if 'model_state_dict' in checkpoint:
            state_dict = checkpoint['model_state_dict']
        elif 'state_dict' in checkpoint:
            state_dict = checkpoint['state_dict']
        else:
            state_dict = checkpoint
        
        # Load state dict
        model.load_state_dict(state_dict, strict=False)
        model.to(self.device)
        model.eval()
        
        return model
    
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
        
        print(f"\nVideo Info:")
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
            
            # Save frame at intervals
            if frame_count % frame_interval == 0:
                frame_path = output_dir / f"frame_{saved_count:04d}.jpg"
                cv2.imwrite(str(frame_path), frame)
                saved_count += 1
                
                if saved_count % 5 == 0:
                    print(f"  Extracted {saved_count} frames...", end='\r')
            
            frame_count += 1
        
        cap.release()
        print(f"\nExtracted {saved_count} frames to {output_dir}")
        return saved_count
    
    def deblur_frame(self, image):
        """Apply deblurring model to a single frame."""
        h, w = image.shape[:2]
        
        # Convert BGR to RGB and normalize
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image_tensor = torch.from_numpy(image_rgb).float().permute(2, 0, 1) / 255.0
        image_tensor = image_tensor.unsqueeze(0).to(self.device)
        
        # Pad to multiple of 8
        pad_h = (8 - h % 8) % 8
        pad_w = (8 - w % 8) % 8
        image_tensor = nn.functional.pad(image_tensor, (0, pad_w, 0, pad_h), mode='reflect')
        
        # Run model
        with torch.no_grad():
            output_tensor = self.model(image_tensor)
            
            # Handle multi-output (take last/best output)
            if isinstance(output_tensor, (list, tuple)):
                output_tensor = output_tensor[-1]
        
        # Remove padding and convert back
        output_tensor = output_tensor[:, :, :h, :w]
        output_img = output_tensor.squeeze(0).permute(1, 2, 0).cpu().numpy()
        output_img = (output_img * 255).clip(0, 255).astype(np.uint8)
        output_img = cv2.cvtColor(output_img, cv2.COLOR_RGB2BGR)
        
        return output_img
    
    def process_frames(self, frames_dir, output_dir):
        """Apply deblurring to all frames."""
        frames_dir = Path(frames_dir)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Get all frames
        frame_files = sorted(frames_dir.glob("*.jpg"))
        total = len(frame_files)
        
        print(f"\nDeblurring {total} frames...")
        
        for i, frame_path in enumerate(frame_files):
            # Load frame
            frame = cv2.imread(str(frame_path))
            
            # Deblur
            deblurred = self.deblur_frame(frame)
            
            # Save
            output_path = output_dir / frame_path.name
            cv2.imwrite(str(output_path), deblurred)
            
            if (i + 1) % 5 == 0 or (i + 1) == total:
                print(f"  Processed {i+1}/{total} frames...", end='\r')
        
        print(f"\nDeblurred frames saved to {output_dir}")
    
    def detect_wagon_numbers(self, images_dir, output_file):
        """Detect wagon numbers using OCR."""
        if self.ocr_reader is None:
            print("\nOCR not available - skipping wagon number detection")
            print("Deblurred frames are saved and ready for manual inspection.")
            return
        
        images_dir = Path(images_dir)
        image_files = sorted(images_dir.glob("*.jpg"))
        
        print(f"\nDetecting wagon numbers in {len(image_files)} frames...")
        
        results = []
        
        for i, img_path in enumerate(image_files):
            # Read image
            img = cv2.imread(str(img_path))
            
            # Run OCR
            try:
                ocr_results = self.ocr_reader.readtext(img)
                
                # Extract potential wagon numbers (4-12 alphanumeric characters)
                wagon_numbers = []
                for bbox, text, confidence in ocr_results:
                    # Clean text
                    text_clean = re.sub(r'[^A-Z0-9]', '', text.upper())
                    
                    # Check if it looks like a wagon number
                    if 4 <= len(text_clean) <= 12 and confidence > 0.5:
                        wagon_numbers.append({
                            'text': text_clean,
                            'confidence': float(confidence),
                            'original': text
                        })
                
                if wagon_numbers:
                    results.append({
                        'frame': img_path.name,
                        'wagon_numbers': wagon_numbers
                    })
                    print(f"  Frame {i+1}: Found {len(wagon_numbers)} potential wagon number(s)")
            
            except Exception as e:
                print(f"  Frame {i+1}: OCR error - {e}")
        
        # Save results
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\nDetection complete! Results saved to {output_file}")
        print(f"Found wagon numbers in {len(results)} frames")


def main():
    """Main processing pipeline."""
    if len(sys.argv) < 3:
        print("Usage: python simple_video_processor.py <video_path> <model_path> [output_dir]")
        print("Example: python simple_video_processor.py 'railway vid 3.mp4' weights/gopro_best.pth output")
        return
    
    video_path = sys.argv[1]
    model_path = sys.argv[2]
    output_dir = sys.argv[3] if len(sys.argv) > 3 else "railway_output"
    
    # Verify inputs
    if not Path(video_path).exists():
        print(f"Error: Video file not found: {video_path}")
        return
    
    if not Path(model_path).exists():
        print(f"Error: Model file not found: {model_path}")
        return
    
    print("=" * 60)
    print("Railway Video Processor")
    print("=" * 60)
    
    # Create output directory structure
    base_output = Path(output_dir)
    frames_dir = base_output / "1_frames"
    deblurred_dir = base_output / "2_deblurred"
    results_file = base_output / "wagon_numbers.json"
    
    # Initialize processor
    processor = SimpleVideoProcessor(model_path)
    
    # Step 1: Extract frames
    print("\n" + "=" * 60)
    print("STEP 1: Extracting Frames (1 FPS)")
    print("=" * 60)
    num_frames = processor.extract_frames(video_path, frames_dir, fps=1)
    
    # Step 2: Deblur frames
    print("\n" + "=" * 60)
    print("STEP 2: Deblurring Frames")
    print("=" * 60)
    processor.process_frames(frames_dir, deblurred_dir)
    
    # Step 3: Detect wagon numbers
    print("\n" + "=" * 60)
    print("STEP 3: Detecting Wagon Numbers")
    print("=" * 60)
    processor.detect_wagon_numbers(deblurred_dir, results_file)
    
    # Summary
    print("\n" + "=" * 60)
    print("PROCESSING COMPLETE!")
    print("=" * 60)
    print(f"\nOutput directory: {base_output}")
    print(f"  - Original frames: {frames_dir}")
    print(f"  - Deblurred frames: {deblurred_dir}")
    if processor.ocr_reader:
        print(f"  - Detection results: {results_file}")
    print("\nYou can now:")
    print(f"  1. View deblurred frames in: {deblurred_dir}")
    if processor.ocr_reader:
        print(f"  2. Check detected wagon numbers in: {results_file}")
    print("=" * 60)


if __name__ == "__main__":
    main()
