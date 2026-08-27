"""
Complete Wagon Inspection Pipeline: Fusion + OCR
=================================================

Runs the complete pipeline:
1. Temporal fusion on multiple frames
2. OCR extraction of wagon number
"""

from temporal_fusion_wagon import TemporalFusionPipeline
from run_ocr_wagon import WagonNumberOCR
import tkinter as tk
from tkinter import filedialog
import os

print("=" * 70)
print("COMPLETE WAGON INSPECTION PIPELINE")
print("=" * 70)
print("\nThis pipeline will:")
print("  1. Select multiple frames")
print("  2. Apply temporal fusion")
print("  3. Extract wagon number via OCR")
print("=" * 70)

# Initialize file dialog
root = tk.Tk()
root.withdraw()
root.attributes('-topmost', True)

# Ask how many frames
num_frames = input("\nHow many frames do you want to fuse (3-5 recommended)? ")
try:
    num_frames = int(num_frames)
    if num_frames < 2:
        print("Need at least 2 frames!")
        exit(1)
except:
    print("Invalid number!")
    exit(1)

# Collect frame paths
frame_paths = []
print(f"\nPlease select {num_frames} frames in order...")

for i in range(num_frames):
    print(f"\nSelecting frame {i+1}/{num_frames}...")
    frame_path = filedialog.askopenfilename(
        title=f"Select frame {i+1} of {num_frames}",
        filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp"), ("All files", "*.*")]
    )
    
    if not frame_path:
        print(f"No file selected for frame {i+1}. Exiting.")
        exit(1)
    
    frame_paths.append(frame_path)
    print(f"  ✓ {os.path.basename(frame_path)}")

# Use max-gradient fusion by default (best for text)
fusion_method = 'max_gradient'

# Choose output directory
output_dir = input("\nOutput directory name [default='wagon_pipeline_results']: ").strip()
if not output_dir:
    output_dir = 'wagon_pipeline_results'

# OCR confidence threshold
ocr_confidence = input("\nOCR confidence threshold [default=0.4]: ").strip()
if not ocr_confidence:
    ocr_confidence = 0.4
else:
    try:
        ocr_confidence = float(ocr_confidence)
    except:
        print("Invalid confidence value, using default 0.4")
        ocr_confidence = 0.4

print("\n" + "=" * 70)
print("PIPELINE CONFIGURATION")
print("=" * 70)
print(f"  Frames: {len(frame_paths)}")
print(f"  Fusion method: {fusion_method.upper()}")
print(f"  OCR confidence: {ocr_confidence}")
print(f"  Output: {output_dir}/")
print("=" * 70)
print()

try:
    # ======================================================================
    # STAGE 1: TEMPORAL FUSION
    # ======================================================================
    
    print("\n" + "=" * 70)
    print("STAGE 1: TEMPORAL FUSION")
    print("=" * 70)
    print()
    
    pipeline = TemporalFusionPipeline(weights_path='weights/gopro_best.pth')
    pipeline.process_sequence(
        frame_paths,
        output_dir=output_dir,
        fusion_method=fusion_method
    )
    
    print("\n✓ Temporal fusion complete")
    
    # ======================================================================
    # STAGE 2: OCR EXTRACTION
    # ======================================================================
    
    print("\n" + "=" * 70)
    print("STAGE 2: OCR EXTRACTION")
    print("=" * 70)
    print()
    
    ocr_input_path = os.path.join(output_dir, 'final_ocr_input.png')
    
    if not os.path.exists(ocr_input_path):
        raise FileNotFoundError(f"OCR input not found: {ocr_input_path}")
    
    ocr = WagonNumberOCR(confidence_threshold=ocr_confidence)
    result = ocr.extract_wagon_number(ocr_input_path, output_dir)
    
    # ======================================================================
    # FINAL SUMMARY
    # ======================================================================
    
    print("\n" + "=" * 70)
    print("PIPELINE COMPLETE - FINAL SUMMARY")
    print("=" * 70)
    print(f"\n📁 Results directory: {output_dir}/")
    print()
    print("🖼️  Image outputs:")
    print(f"  - final_ocr_input.png       (Enhanced fused image)")
    print(f"  - ocr_visualization.png     (OCR bounding boxes)")
    print(f"  - comparison_grid.png       (Before/after comparison)")
    print()
    print("🔢 Wagon Number Extraction:")
    print(f"  - Number:     {result['wagon_number']}")
    print(f"  - Confidence: {result['confidence']:.3f}")
    print(f"  - Status:     {'✓ READABLE' if result['is_valid'] else '⚠ UNREADABLE'}")
    print()
    print("=" * 70)
    
    if result['wagon_number'] != 'UNREADABLE':
        print("\n✓ SUCCESS: Wagon number extracted successfully!")
    else:
        print("\n⚠ WARNING: Wagon number could not be read reliably.")
        print("  This is expected for heavily blurred or obscured images.")
        print("  The system prioritizes correctness over guessing.")
    
    print()
    
except Exception as e:
    print("\n" + "=" * 70)
    print("ERROR!")
    print("=" * 70)
    print(f"\n{e}")
    import traceback
    traceback.print_exc()
    print("\n" + "=" * 70)
