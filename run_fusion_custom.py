"""
Run Temporal Fusion on Your Dataset
====================================

Simple script to run temporal fusion on your own images.
"""

from temporal_fusion_wagon import TemporalFusionPipeline
import tkinter as tk
from tkinter import filedialog
import os

print("=" * 70)
print("TEMPORAL FUSION - CUSTOM DATASET")
print("=" * 70)
print("\nThis will help you select multiple consecutive frames to fuse.")
print("\nMake sure your frames are:")
print("  - From the same camera viewpoint")
print("  - Consecutive or near-consecutive")
print("  - Showing the same wagon number")
print("  - 3-5 frames total (5 recommended)")
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
output_dir = input("\nOutput directory name [default='my_fusion_results']: ").strip()
if not output_dir:
    output_dir = 'my_fusion_results'

# Run the pipeline
print("\n" + "=" * 70)
print("RUNNING TEMPORAL FUSION")
print("=" * 70)
print(f"\nFrames: {len(frame_paths)}")
print(f"Method: {fusion_method.upper()}")
print(f"Output: {output_dir}/")
print()

try:
    pipeline = TemporalFusionPipeline(weights_path='weights/gopro_best.pth')
    pipeline.process_sequence(
        frame_paths,
        output_dir=output_dir,
        fusion_method=fusion_method
    )
    
    print("\n" + "=" * 70)
    print("SUCCESS!")
    print("=" * 70)
    print(f"\nCheck your results in: {output_dir}/")
    print("\nKey files:")
    print(f"  - {output_dir}/final_ocr_input.png       ← Use for OCR")
    print(f"  - {output_dir}/enhanced_fused_band.png   ← Visual quality")
    print(f"  - {output_dir}/comparison_grid.png       ← See improvement")
    print("=" * 70)
    
except Exception as e:
    print("\n" + "=" * 70)
    print("ERROR!")
    print("=" * 70)
    print(f"\n{e}")
    import traceback
    traceback.print_exc()
    print("\n" + "=" * 70)
