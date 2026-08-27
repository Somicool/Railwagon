"""
Wagon Number Band Extraction Module
====================================
Extracts horizontal band region where wagon numbers typically appear.

Uses structural prior:
- Height: 40% to 60% of image height
- Width: 10% to 90% of image width

Author: Railway Wagon Inspection System
Date: 2025-12-22
"""

import cv2
import numpy as np
from pathlib import Path
from tqdm import tqdm


class WagonBandExtractor:
    """Extract wagon number band from enhanced frames."""
    
    def __init__(self, output_dir, height_range=(0.4, 0.6), width_range=(0.1, 0.9)):
        """
        Initialize band extractor with structural constraints.
        
        Args:
            output_dir (str): Directory to save band images
            height_range (tuple): (min_fraction, max_fraction) for height crop
            width_range (tuple): (min_fraction, max_fraction) for width crop
        """
        self.output_dir = Path(output_dir)
        self.height_range = height_range
        self.width_range = width_range
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"Wagon Band Extractor initialized:")
        print(f"  - Height range: {height_range[0]:.1%} to {height_range[1]:.1%}")
        print(f"  - Width range: {width_range[0]:.1%} to {width_range[1]:.1%}")
        print(f"  - Output: {self.output_dir}")
    
    def extract_band(self, frame_path):
        """
        Extract wagon number band from a single frame.
        
        Args:
            frame_path (str): Path to enhanced frame
            
        Returns:
            str: Path to extracted band image
        """
        # Read frame
        frame = cv2.imread(frame_path)
        
        if frame is None:
            raise ValueError(f"Cannot read frame: {frame_path}")
        
        h, w = frame.shape[:2]
        
        # Calculate crop coordinates based on structural prior
        y1 = int(h * self.height_range[0])
        y2 = int(h * self.height_range[1])
        x1 = int(w * self.width_range[0])
        x2 = int(w * self.width_range[1])
        
        # Crop band region
        band = frame[y1:y2, x1:x2]
        
        # Save band with same filename
        frame_name = Path(frame_path).name
        output_path = self.output_dir / frame_name
        cv2.imwrite(str(output_path), band)
        
        return str(output_path)
    
    def extract_bands(self, frame_paths):
        """
        Extract wagon number bands from multiple frames.
        
        Args:
            frame_paths (list): List of enhanced frame paths
            
        Returns:
            list: List of band image paths
        """
        band_paths = []
        
        print(f"\nExtracting wagon number bands from {len(frame_paths)} frames...")
        
        for frame_path in tqdm(frame_paths, desc="Extracting bands"):
            try:
                band_path = self.extract_band(frame_path)
                band_paths.append(band_path)
            except Exception as e:
                print(f"Error extracting band from {frame_path}: {e}")
                continue
        
        print(f"✓ Extracted {len(band_paths)} bands -> {self.output_dir}")
        
        return band_paths
    
    def visualize_crop_region(self, frame_path, output_path=None):
        """
        Visualize the crop region on a sample frame.
        
        Args:
            frame_path (str): Path to frame
            output_path (str): Optional path to save visualization
            
        Returns:
            np.ndarray: Visualized frame with crop rectangle
        """
        frame = cv2.imread(frame_path)
        h, w = frame.shape[:2]
        
        # Calculate crop coordinates
        y1 = int(h * self.height_range[0])
        y2 = int(h * self.height_range[1])
        x1 = int(w * self.width_range[0])
        x2 = int(w * self.width_range[1])
        
        # Draw rectangle
        vis_frame = frame.copy()
        cv2.rectangle(vis_frame, (x1, y1), (x2, y2), (0, 255, 0), 3)
        
        # Add text
        cv2.putText(vis_frame, "Wagon Number Search Band", 
                    (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 
                    1.0, (0, 255, 0), 2)
        
        if output_path:
            cv2.imwrite(output_path, vis_frame)
            print(f"Visualization saved to {output_path}")
        
        return vis_frame


def extract_wagon_bands(frame_dir, output_dir="results/band_frames", 
                        height_range=(0.4, 0.6), width_range=(0.1, 0.9)):
    """
    Convenience function to extract wagon bands from all frames.
    
    Args:
        frame_dir (str): Directory containing enhanced frames
        output_dir (str): Directory to save band images
        height_range (tuple): Height crop range (fraction)
        width_range (tuple): Width crop range (fraction)
        
    Returns:
        list: List of band image paths
    """
    # Get all frame paths
    frame_dir = Path(frame_dir)
    frame_paths = sorted(frame_dir.glob("*.png"))
    frame_paths = [str(p) for p in frame_paths]
    
    if not frame_paths:
        print(f"No frames found in {frame_dir}")
        return []
    
    # Create extractor and process
    extractor = WagonBandExtractor(output_dir, height_range, width_range)
    return extractor.extract_bands(frame_paths)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python extract_bands.py <frame_dir> [output_dir] [visualize]")
        print("Example: python extract_bands.py results/enhanced_frames results/band_frames")
        print("Example: python extract_bands.py results/enhanced_frames results/band_frames visualize")
        sys.exit(1)
    
    frame_dir = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "results/band_frames"
    visualize = len(sys.argv) > 3 and sys.argv[3] == "visualize"
    
    # Extract bands
    band_paths = extract_wagon_bands(frame_dir, output_dir)
    print(f"Extracted {len(band_paths)} wagon bands")
    
    # Optional: visualize crop region on first frame
    if visualize and band_paths:
        frame_paths = sorted(Path(frame_dir).glob("*.png"))
        if frame_paths:
            extractor = WagonBandExtractor(output_dir)
            extractor.visualize_crop_region(
                str(frame_paths[0]), 
                "results/crop_visualization.png"
            )
