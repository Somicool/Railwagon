"""
Video-to-Wagon-OCR Complete Pipeline
=====================================
Automated railway wagon inspection system that processes train videos
and extracts wagon numbers using temporal fusion and OCR.

PIPELINE STAGES:
1. Video → Frames extraction (configurable FPS)
2. Per-frame global enhancement (deblurring model)
3. Wagon-number band extraction (structural prior)
4. Temporal fusion (multi-frame alignment + median)
5. Text-specific enhancement (CLAHE + sharpening)
6. OCR (EasyOCR or Tesseract)
7. Results saved to organized folder structure

Author: Railway Wagon Inspection System
Date: 2025-12-22
"""

import argparse
import torch
from pathlib import Path
import time

# Import pipeline modules
from video_to_frames import extract_video_frames
from process_frames import enhance_all_frames
from extract_bands import extract_wagon_bands
from temporal_fusion import fuse_temporal_sequence
from text_enhancement import enhance_for_text_ocr
from ocr_pipeline import run_ocr_pipeline


class WagonInspectionPipeline:
    """Complete video-to-OCR pipeline for railway wagon inspection."""
    
    def __init__(self, video_path, model_path, output_dir="results",
                 fps=5, window_size=3, ocr_engine='easyocr', 
                 min_confidence=0.3, device='cuda'):
        """
        Initialize complete pipeline.
        
        Args:
            video_path (str): Path to input video file
            model_path (str): Path to deblurring model weights
            output_dir (str): Root directory for all outputs
            fps (int): Target FPS for frame extraction
            window_size (int): Temporal fusion window size
            ocr_engine (str): 'easyocr' or 'tesseract'
            min_confidence (float): OCR confidence threshold
            device (str): 'cuda' or 'cpu'
        """
        self.video_path = video_path
        self.model_path = model_path
        self.output_dir = Path(output_dir)
        self.fps = fps
        self.window_size = window_size
        self.ocr_engine = ocr_engine
        self.min_confidence = min_confidence
        self.device = device if torch.cuda.is_available() else 'cpu'
        
        # Create output directory structure
        self.dirs = {
            'raw_frames': self.output_dir / "1_raw_frames",
            'enhanced_frames': self.output_dir / "2_enhanced_frames",
            'band_frames': self.output_dir / "3_band_frames",
            'fused': self.output_dir / "4_fused",
            'enhanced_text': self.output_dir / "5_enhanced_text",
            'ocr_results': self.output_dir / "6_ocr_results"
        }
        
        for dir_path in self.dirs.values():
            dir_path.mkdir(parents=True, exist_ok=True)
        
        print("="*70)
        print("WAGON INSPECTION PIPELINE INITIALIZED")
        print("="*70)
        print(f"Input video: {video_path}")
        print(f"Model: {model_path}")
        print(f"Output directory: {output_dir}")
        print(f"Device: {self.device}")
        print(f"Frame extraction: {fps} FPS")
        print(f"Temporal fusion: {window_size} frames")
        print(f"OCR engine: {ocr_engine}")
        print("="*70)
    
    def run(self):
        """Execute complete pipeline."""
        
        start_time = time.time()
        
        # Stage 1: Extract frames from video
        print("\n" + "="*70)
        print("STAGE 1: VIDEO TO FRAMES EXTRACTION")
        print("="*70)
        
        frame_paths = extract_video_frames(
            self.video_path,
            str(self.dirs['raw_frames']),
            self.fps
        )
        
        if not frame_paths:
            print("ERROR: No frames extracted from video!")
            return None
        
        # Stage 2: Per-frame enhancement
        print("\n" + "="*70)
        print("STAGE 2: PER-FRAME GLOBAL ENHANCEMENT")
        print("="*70)
        
        enhanced_paths = enhance_all_frames(
            str(self.dirs['raw_frames']),
            self.model_path,
            str(self.dirs['enhanced_frames']),
            self.device
        )
        
        if not enhanced_paths:
            print("ERROR: No frames enhanced!")
            return None
        
        # Stage 3: Extract wagon number bands
        print("\n" + "="*70)
        print("STAGE 3: WAGON NUMBER BAND EXTRACTION")
        print("="*70)
        
        band_paths = extract_wagon_bands(
            str(self.dirs['enhanced_frames']),
            str(self.dirs['band_frames'])
        )
        
        if not band_paths:
            print("ERROR: No bands extracted!")
            return None
        
        # Stage 4: Temporal fusion
        print("\n" + "="*70)
        print("STAGE 4: TEMPORAL FUSION")
        print("="*70)
        
        fused_paths = fuse_temporal_sequence(
            str(self.dirs['band_frames']),
            str(self.dirs['fused']),
            self.window_size
        )
        
        if not fused_paths:
            print("ERROR: Temporal fusion failed!")
            return None
        
        # Stage 5: Text-specific enhancement
        print("\n" + "="*70)
        print("STAGE 5: TEXT-SPECIFIC ENHANCEMENT")
        print("="*70)
        
        color_paths, gray_paths = enhance_for_text_ocr(
            str(self.dirs['fused']),
            str(self.dirs['enhanced_text'])
        )
        
        if not gray_paths:
            print("ERROR: Text enhancement failed!")
            return None
        
        # Stage 6: OCR
        print("\n" + "="*70)
        print("STAGE 6: OCR (WAGON NUMBER EXTRACTION)")
        print("="*70)
        
        ocr_results = run_ocr_pipeline(
            str(self.dirs['enhanced_text']),
            str(self.dirs['ocr_results']),
            self.ocr_engine,
            self.min_confidence,
            gpu=(self.device == 'cuda')
        )
        
        # Pipeline complete
        elapsed_time = time.time() - start_time
        
        print("\n" + "="*70)
        print("PIPELINE COMPLETE!")
        print("="*70)
        print(f"Total time: {elapsed_time:.2f} seconds")
        print(f"Frames processed: {len(frame_paths)}")
        print(f"Fused images: {len(fused_paths)}")
        print(f"OCR results: {len(ocr_results)}")
        
        # Summary
        detected = sum(1 for r in ocr_results if r.get('best_wagon_number'))
        print(f"Wagon numbers detected: {detected}/{len(ocr_results)}")
        print(f"\nAll results saved to: {self.output_dir}")
        print("="*70)
        
        # Print detected wagon numbers
        if detected > 0:
            print("\nDETECTED WAGON NUMBERS:")
            print("-" * 50)
            for i, result in enumerate(ocr_results):
                if result.get('best_wagon_number'):
                    wagon = result['best_wagon_number']
                    print(f"{i+1}. {wagon['number']} (confidence: {wagon['confidence']:.3f})")
        
        return ocr_results


def main():
    """Main entry point with command-line interface."""
    
    parser = argparse.ArgumentParser(
        description="Railway Wagon Inspection: Video-to-OCR Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
EXAMPLE USAGE:
--------------
Basic usage:
  python run_video_pipeline.py train_video.mp4 weights/gopro_best.pth

Custom settings:
  python run_video_pipeline.py train_video.mp4 weights/gopro_best.pth \\
      --output wagon_results --fps 10 --window 5 --ocr tesseract

Full options:
  python run_video_pipeline.py train_video.mp4 weights/gopro_best.pth \\
      --output results --fps 5 --window 3 --ocr easyocr \\
      --confidence 0.3 --device cuda

OUTPUT STRUCTURE:
-----------------
results/
├── 1_raw_frames/         # Extracted video frames
├── 2_enhanced_frames/    # Deblurred frames
├── 3_band_frames/        # Wagon number search bands
├── 4_fused/              # Temporally fused images
├── 5_enhanced_text/      # OCR-optimized images
└── 6_ocr_results/        # Final OCR outputs
    ├── ocr_results.json  # Detailed JSON results
    ├── ocr_results.txt   # Human-readable summary
    └── ocr_visuals/      # Visualizations with bounding boxes
        """
    )
    
    # Required arguments
    parser.add_argument('video', help='Path to input video file (MP4)')
    parser.add_argument('model', help='Path to deblurring model weights (.pth)')
    
    # Optional arguments
    parser.add_argument('--output', '-o', default='results',
                       help='Output directory for all results (default: results)')
    parser.add_argument('--fps', type=int, default=5,
                       help='Target FPS for frame extraction (default: 5)')
    parser.add_argument('--window', '-w', type=int, default=3,
                       help='Temporal fusion window size (3-5 recommended, default: 3)')
    parser.add_argument('--ocr', choices=['easyocr', 'tesseract'], default='easyocr',
                       help='OCR engine to use (default: easyocr)')
    parser.add_argument('--confidence', '-c', type=float, default=0.3,
                       help='Minimum OCR confidence threshold 0.0-1.0 (default: 0.3)')
    parser.add_argument('--device', choices=['cuda', 'cpu'], default='cuda',
                       help='Device for model inference (default: cuda)')
    
    args = parser.parse_args()
    
    # Validate inputs
    if not Path(args.video).exists():
        print(f"ERROR: Video file not found: {args.video}")
        return
    
    if not Path(args.model).exists():
        print(f"ERROR: Model weights not found: {args.model}")
        return
    
    # Create and run pipeline
    pipeline = WagonInspectionPipeline(
        video_path=args.video,
        model_path=args.model,
        output_dir=args.output,
        fps=args.fps,
        window_size=args.window,
        ocr_engine=args.ocr,
        min_confidence=args.confidence,
        device=args.device
    )
    
    results = pipeline.run()
    
    if results is not None:
        print("\n✓ Pipeline executed successfully!")
    else:
        print("\n✗ Pipeline failed!")


if __name__ == "__main__":
    main()
