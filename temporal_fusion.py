"""
Temporal Fusion Module
======================
Aligns and fuses consecutive frames using sliding window and median fusion.

WHY TEMPORAL FUSION?
--------------------
In high-speed railway wagon inspection:
1. Motion blur varies across frames due to camera shake and wagon speed
2. Different frames capture slightly different perspectives of the same wagon
3. Temporal redundancy can be exploited to reduce noise and motion blur
4. Median fusion suppresses outliers (e.g., reflections, shadows)
5. Multi-frame fusion improves text clarity for OCR

APPROACH:
---------
- Sliding window of 3-5 consecutive frames
- Phase correlation for horizontal alignment (trains move horizontally)
- Pixel-wise median to suppress outliers and reduce blur
- No GANs, no hallucination - pure signal processing

Author: Railway Wagon Inspection System
Date: 2025-12-22
"""

import cv2
import numpy as np
from pathlib import Path
from tqdm import tqdm


class TemporalFusion:
    """Align and fuse consecutive frames for improved quality."""
    
    def __init__(self, output_dir, window_size=3, alignment_method='phase_correlation'):
        """
        Initialize temporal fusion.
        
        Args:
            output_dir (str): Directory to save fused images
            window_size (int): Number of consecutive frames to fuse (3-5)
            alignment_method (str): 'phase_correlation' or 'none'
        """
        self.output_dir = Path(output_dir)
        self.window_size = window_size
        self.alignment_method = alignment_method
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"Temporal Fusion initialized:")
        print(f"  - Window size: {window_size} frames")
        print(f"  - Alignment: {alignment_method}")
        print(f"  - Output: {self.output_dir}")
    
    def align_images(self, reference, image):
        """
        Align image to reference using phase correlation.
        
        Args:
            reference (np.ndarray): Reference image
            image (np.ndarray): Image to align
            
        Returns:
            np.ndarray: Aligned image
        """
        if self.alignment_method == 'none':
            return image
        
        # Convert to grayscale for alignment
        ref_gray = cv2.cvtColor(reference, cv2.COLOR_BGR2GRAY)
        img_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Phase correlation to find shift
        # This is efficient for pure translation (horizontal motion)
        shift, _ = cv2.phaseCorrelate(
            ref_gray.astype(np.float32),
            img_gray.astype(np.float32)
        )
        
        # Round to nearest pixel
        shift_x = int(round(shift[0]))
        shift_y = int(round(shift[1]))
        
        # Only apply horizontal shift (trains move horizontally)
        # Ignore vertical shift to avoid misalignment
        shift_y = 0
        
        # Apply translation
        h, w = image.shape[:2]
        M = np.float32([[1, 0, shift_x], [0, 1, shift_y]])
        aligned = cv2.warpAffine(image, M, (w, h), 
                                 flags=cv2.INTER_LINEAR,
                                 borderMode=cv2.BORDER_REPLICATE)
        
        return aligned
    
    def fuse_frames(self, frames):
        """
        Fuse multiple frames using pixel-wise median.
        
        Args:
            frames (list): List of aligned frames (numpy arrays)
            
        Returns:
            np.ndarray: Fused frame
        """
        if len(frames) == 0:
            return None
        
        if len(frames) == 1:
            return frames[0]
        
        # Stack frames along new axis
        stack = np.stack(frames, axis=0)  # [N, H, W, C]
        
        # Compute pixel-wise median
        # This suppresses outliers and reduces noise
        fused = np.median(stack, axis=0).astype(np.uint8)
        
        return fused
    
    def process_window(self, band_paths, window_start, window_end):
        """
        Process a single sliding window.
        
        Args:
            band_paths (list): All band image paths
            window_start (int): Start index of window
            window_end (int): End index of window
            
        Returns:
            tuple: (fused_image, center_index)
        """
        # Load frames in window
        frames = []
        for i in range(window_start, window_end):
            if i < len(band_paths):
                frame = cv2.imread(band_paths[i])
                if frame is not None:
                    frames.append(frame)
        
        if not frames:
            return None, None
        
        # Use middle frame as reference for alignment
        reference_idx = len(frames) // 2
        reference = frames[reference_idx]
        
        # Align all frames to reference
        aligned_frames = [reference]  # Reference is already aligned
        
        for i, frame in enumerate(frames):
            if i != reference_idx:
                aligned = self.align_images(reference, frame)
                aligned_frames.append(aligned)
        
        # Fuse aligned frames
        fused = self.fuse_frames(aligned_frames)
        
        # Center index in original sequence
        center_idx = window_start + reference_idx
        
        return fused, center_idx
    
    def fuse_sequence(self, band_paths):
        """
        Apply temporal fusion to sequence of band images.
        
        Args:
            band_paths (list): List of band image paths (sorted)
            
        Returns:
            list: List of fused image paths
        """
        if len(band_paths) < self.window_size:
            print(f"Warning: Only {len(band_paths)} frames, window size is {self.window_size}")
            print("Fusing all available frames...")
            
        fused_paths = []
        
        print(f"\nFusing {len(band_paths)} frames with window size {self.window_size}...")
        
        # Sliding window
        stride = 1  # Can be adjusted for faster processing
        num_windows = max(1, (len(band_paths) - self.window_size) // stride + 1)
        
        for i in tqdm(range(num_windows), desc="Temporal fusion"):
            window_start = i * stride
            window_end = min(window_start + self.window_size, len(band_paths))
            
            # Process window
            fused, center_idx = self.process_window(band_paths, window_start, window_end)
            
            if fused is not None:
                # Save fused image
                output_name = f"fused_{center_idx:04d}.png"
                output_path = self.output_dir / output_name
                cv2.imwrite(str(output_path), fused)
                fused_paths.append(str(output_path))
        
        print(f"✓ Generated {len(fused_paths)} fused frames -> {self.output_dir}")
        
        return fused_paths


def fuse_temporal_sequence(band_dir, output_dir="results/fused", 
                           window_size=3, alignment='phase_correlation'):
    """
    Convenience function for temporal fusion.
    
    Args:
        band_dir (str): Directory containing band images
        output_dir (str): Directory to save fused images
        window_size (int): Sliding window size (3-5 recommended)
        alignment (str): Alignment method
        
    Returns:
        list: List of fused image paths
    """
    # Get all band paths (sorted)
    band_dir = Path(band_dir)
    band_paths = sorted(band_dir.glob("*.png"))
    band_paths = [str(p) for p in band_paths]
    
    if not band_paths:
        print(f"No band images found in {band_dir}")
        return []
    
    # Create fusion processor
    fusion = TemporalFusion(output_dir, window_size, alignment)
    return fusion.fuse_sequence(band_paths)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python temporal_fusion.py <band_dir> [output_dir] [window_size]")
        print("Example: python temporal_fusion.py results/band_frames results/fused 3")
        sys.exit(1)
    
    band_dir = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "results/fused"
    window_size = int(sys.argv[3]) if len(sys.argv) > 3 else 3
    
    fused_paths = fuse_temporal_sequence(band_dir, output_dir, window_size)
    print(f"Generated {len(fused_paths)} fused images")
    
    print("\n" + "="*60)
    print("WHY TEMPORAL FUSION HELPS:")
    print("="*60)
    print("1. Reduces motion blur by combining multiple perspectives")
    print("2. Suppresses noise and reflections using median filtering")
    print("3. Improves text clarity without hallucinating details")
    print("4. Exploits temporal redundancy in video sequences")
    print("5. More robust than single-frame enhancement for OCR")
    print("="*60)
