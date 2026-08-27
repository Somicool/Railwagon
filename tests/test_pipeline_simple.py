"""
Quick test of the video pipeline WITHOUT deblurring step
Tests: video extraction -> band extraction -> temporal fusion -> text enhancement -> OCR
"""

import sys
sys.path.insert(0, '.')

from video_to_frames import extract_video_frames
from extract_bands import extract_wagon_bands  
from temporal_fusion import fuse_temporal_sequence
from text_enhancement import enhance_for_text_ocr
from ocr_pipeline import run_ocr_pipeline
from pathlib import Path

print("="*70)
print("VIDEO PIPELINE TEST (WITHOUT DEBLURRING)")
print("="*70)

# Config
video_path = "test_video.mp4"
output_dir = Path("test_results_simple")

# Create output dirs
dirs = {
    'raw_frames': output_dir / "1_raw_frames",
    'band_frames': output_dir / "2_band_frames",
    'fused': output_dir / "3_fused",
    'enhanced_text': output_dir / "4_enhanced_text",
    'ocr_results': output_dir / "5_ocr_results"
}

for d in dirs.values():
    d.mkdir(parents=True, exist_ok=True)

# Step 1: Extract frames
print("\nSTEP 1: Extract frames")
frame_paths = extract_video_frames(video_path, str(dirs['raw_frames']), target_fps=5)

# Step 2: Extract wagon bands (skip deblurring, use raw frames)
print("\nSTEP 2: Extract wagon number bands")
band_paths = extract_wagon_bands(str(dirs['raw_frames']), str(dirs['band_frames']))

# Step 3: Temporal fusion
print("\nSTEP 3: Temporal fusion")
fused_paths = fuse_temporal_sequence(str(dirs['band_frames']), str(dirs['fused']), window_size=3)

# Step 4: Text enhancement
print("\nSTEP 4: Text enhancement for OCR")
color_paths, gray_paths = enhance_for_text_ocr(str(dirs['fused']), str(dirs['enhanced_text']))

# Step 5: OCR
print("\nSTEP 5: OCR")
ocr_results = run_ocr_pipeline(str(dirs['enhanced_text']), str(dirs['ocr_results']), 
                               ocr_engine='easyocr', min_confidence=0.2, gpu=True)

# Summary
print("\n" + "="*70)
print("TEST COMPLETE!")
print("="*70)
print(f"Frames extracted: {len(frame_paths)}")
print(f"Bands extracted: {len(band_paths)}")
print(f"Fused images: {len(fused_paths)}")
print(f"OCR results: {len(ocr_results)}")

detected = sum(1 for r in ocr_results if r.get('best_wagon_number'))
print(f"Wagon numbers detected: {detected}/{len(ocr_results)}")

print(f"\nResults in: {output_dir}")
print("="*70)
