"""
Quick Video Pipeline Tester
============================
Easy way to test the pipeline with your own video.

Just run: python test_my_video.py <your_video_path>
"""

import sys
import os
from pathlib import Path

# Import pipeline modules
from video_to_frames import extract_video_frames
from extract_bands import extract_wagon_bands
from temporal_fusion import fuse_temporal_sequence
from text_enhancement import enhance_for_text_ocr
from ocr_pipeline import run_ocr_pipeline


def test_video_pipeline(video_path, output_dir="my_video_results"):
    """Test pipeline on your video without deblurring step."""
    
    print("="*70)
    print("TESTING YOUR VIDEO")
    print("="*70)
    print(f"Video: {video_path}")
    print(f"Output: {output_dir}")
    print("="*70)
    
    # Create output directories
    output_dir = Path(output_dir)
    dirs = {
        'raw_frames': output_dir / "1_raw_frames",
        'band_frames': output_dir / "2_band_frames",
        'fused': output_dir / "3_fused",
        'enhanced_text': output_dir / "4_enhanced_text",
        'ocr_results': output_dir / "5_ocr_results"
    }
    
    for d in dirs.values():
        d.mkdir(parents=True, exist_ok=True)
    
    # STEP 1: Extract frames
    print("\nSTEP 1: Extracting frames from video...")
    frame_paths = extract_video_frames(
        video_path,
        str(dirs['raw_frames']),
        target_fps=5  # Adjust if needed
    )
    
    if not frame_paths:
        print("ERROR: No frames extracted!")
        return
    
    # STEP 2: Extract wagon number bands
    print("\nSTEP 2: Extracting wagon number bands...")
    band_paths = extract_wagon_bands(
        str(dirs['raw_frames']),
        str(dirs['band_frames']),
        height_range=(0.4, 0.6),  # Adjust if wagon numbers are elsewhere
        width_range=(0.1, 0.9)
    )
    
    if not band_paths:
        print("ERROR: No bands extracted!")
        return
    
    # STEP 3: Temporal fusion
    print("\nSTEP 3: Applying temporal fusion...")
    fused_paths = fuse_temporal_sequence(
        str(dirs['band_frames']),
        str(dirs['fused']),
        window_size=3  # Increase for more blur reduction
    )
    
    if not fused_paths:
        print("ERROR: Fusion failed!")
        return
    
    # STEP 4: Text enhancement
    print("\nSTEP 4: Enhancing for OCR...")
    color_paths, gray_paths = enhance_for_text_ocr(
        str(dirs['fused']),
        str(dirs['enhanced_text']),
        clahe_clip=2.0,
        sharpen_strength=0.3
    )
    
    if not gray_paths:
        print("ERROR: Enhancement failed!")
        return
    
    # STEP 5: OCR
    print("\nSTEP 5: Running OCR...")
    ocr_results = run_ocr_pipeline(
        str(dirs['enhanced_text']),
        str(dirs['ocr_results']),
        ocr_engine='easyocr',
        min_confidence=0.2,  # Lower = more detections
        gpu=True
    )
    
    # Print results
    print("\n" + "="*70)
    print("RESULTS")
    print("="*70)
    print(f"Frames extracted: {len(frame_paths)}")
    print(f"Bands extracted: {len(band_paths)}")
    print(f"Fused images: {len(fused_paths)}")
    print(f"OCR processed: {len(ocr_results)}")
    
    detected = sum(1 for r in ocr_results if r.get('best_wagon_number'))
    print(f"Wagon numbers detected: {detected}/{len(ocr_results)}")
    
    if detected > 0:
        print("\nDETECTED WAGON NUMBERS:")
        print("-" * 50)
        for i, result in enumerate(ocr_results):
            if result.get('best_wagon_number'):
                wagon = result['best_wagon_number']
                print(f"{i+1}. {wagon['number']} (confidence: {wagon['confidence']:.3f})")
    
    print(f"\nAll results saved to: {output_dir}")
    print(f"Check OCR results: {dirs['ocr_results']}/ocr_results.txt")
    print(f"View visualizations: {dirs['ocr_results']}/ocr_visuals/")
    print("="*70)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("\n" + "="*70)
        print("USAGE")
        print("="*70)
        print("python test_my_video.py <video_path> [output_dir]")
        print("\nEXAMPLES:")
        print("  python test_my_video.py my_train_video.mp4")
        print("  python test_my_video.py C:/Videos/train.mp4")
        print("  python test_my_video.py my_video.mp4 custom_results")
        print("\nCURRENT DIRECTORY:")
        print(f"  {os.getcwd()}")
        print("\nAVAILABLE VIDEOS IN THIS FOLDER:")
        videos = list(Path('.').glob('*.mp4')) + list(Path('.').glob('*.avi')) + list(Path('.').glob('*.mov'))
        if videos:
            for v in videos:
                print(f"  - {v}")
        else:
            print("  (none found - add your video file here)")
        print("="*70)
        sys.exit(1)
    
    video_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "my_video_results"
    
    if not os.path.exists(video_path):
        print(f"\nERROR: Video file not found: {video_path}")
        print("Please check the path and try again.")
        sys.exit(1)
    
    test_video_pipeline(video_path, output_dir)
