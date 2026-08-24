"""
Video to Frames Extraction Module
==================================
Extracts frames from input video at configurable FPS for wagon inspection pipeline.

Author: Railway Wagon Inspection System
Date: 2025-12-22
"""

import cv2
import os
from pathlib import Path
import numpy as np


class VideoFrameExtractor:
    """Extract frames from video at specified FPS."""
    
    def __init__(self, video_path, output_dir, target_fps=5):
        """
        Initialize video frame extractor.
        
        Args:
            video_path (str): Path to input video file
            output_dir (str): Directory to save extracted frames
            target_fps (int): Target frames per second to extract (default: 5)
        """
        self.video_path = video_path
        self.output_dir = Path(output_dir)
        self.target_fps = target_fps
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def extract_frames(self):
        """
        Extract frames from video at target FPS.
        
        Returns:
            list: List of saved frame paths
        """
        # Open video
        cap = cv2.VideoCapture(self.video_path)
        
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {self.video_path}")
        
        # Get video properties
        video_fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / video_fps if video_fps > 0 else 0
        
        print(f"Video Properties:")
        print(f"  - FPS: {video_fps:.2f}")
        print(f"  - Total Frames: {total_frames}")
        print(f"  - Duration: {duration:.2f} seconds")
        print(f"  - Target FPS: {self.target_fps}")
        
        # Calculate frame interval
        if self.target_fps >= video_fps:
            frame_interval = 1  # Extract all frames
            print(f"  - Extracting all frames (target FPS >= video FPS)")
        else:
            frame_interval = int(video_fps / self.target_fps)
            print(f"  - Frame interval: every {frame_interval} frames")
        
        # Extract frames
        frame_count = 0
        saved_count = 0
        saved_paths = []
        
        while True:
            ret, frame = cap.read()
            
            if not ret:
                break
            
            # Save frame at specified interval
            if frame_count % frame_interval == 0:
                # Generate filename with zero-padded numbering
                filename = f"frame_{saved_count:04d}.png"
                output_path = self.output_dir / filename
                
                # Save frame
                cv2.imwrite(str(output_path), frame)
                saved_paths.append(str(output_path))
                saved_count += 1
                
                if saved_count % 10 == 0:
                    print(f"  - Extracted {saved_count} frames...", end='\r')
            
            frame_count += 1
        
        cap.release()
        
        print(f"\n✓ Extraction complete: {saved_count} frames saved to {self.output_dir}")
        
        return saved_paths


def extract_video_frames(video_path, output_dir="results/raw_frames", target_fps=5):
    """
    Convenience function to extract frames from video.
    
    Args:
        video_path (str): Path to input video file
        output_dir (str): Directory to save extracted frames
        target_fps (int): Target frames per second to extract
        
    Returns:
        list: List of saved frame paths
    """
    extractor = VideoFrameExtractor(video_path, output_dir, target_fps)
    return extractor.extract_frames()


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python video_to_frames.py <video_path> [output_dir] [fps]")
        print("Example: python video_to_frames.py train_video.mp4 results/raw_frames 5")
        sys.exit(1)
    
    video_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "results/raw_frames"
    target_fps = int(sys.argv[3]) if len(sys.argv) > 3 else 5
    
    print(f"Extracting frames from: {video_path}")
    frame_paths = extract_video_frames(video_path, output_dir, target_fps)
    print(f"Saved {len(frame_paths)} frames")
