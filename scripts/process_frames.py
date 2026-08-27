"""
Per-Frame Enhancement Module
=============================
Applies global enhancement/deblurring to each extracted frame.

Author: Railway Wagon Inspection System
Date: 2025-12-22
"""

import cv2
import torch
import numpy as np
from pathlib import Path
import os
from tqdm import tqdm


class FrameEnhancer:
    """Apply deblurring model to frames."""
    
    def __init__(self, model_path, output_dir, device='cuda'):
        """
        Initialize frame enhancer with deblurring model.
        
        Args:
            model_path (str): Path to trained model weights
            output_dir (str): Directory to save enhanced frames
            device (str): 'cuda' or 'cpu'
        """
        self.model_path = model_path
        self.output_dir = Path(output_dir)
        self.device = device if torch.cuda.is_available() else 'cpu'
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load model
        self.model = self._load_model()
        
        print(f"Frame Enhancer initialized:")
        print(f"  - Model: {model_path}")
        print(f"  - Device: {self.device}")
        print(f"  - Output: {self.output_dir}")
    
    def _load_model(self):
        """Load deblurring model."""
        from models.mimo_unet_plus import MIMOUNetPlus
        
        model = MIMOUNetPlus()
        
        # Load weights
        checkpoint = torch.load(self.model_path, map_location=self.device, weights_only=False)
        
        # Handle different checkpoint formats
        if isinstance(checkpoint, dict) and 'model_state_dict' in checkpoint:
            model.load_state_dict(checkpoint['model_state_dict'])
        else:
            model.load_state_dict(checkpoint)
        
        model = model.to(self.device)
        model.eval()
        
        print("  - Model loaded: MIMO-UNet+")
        
        return model
    
    def _preprocess(self, image):
        """
        Preprocess image for model input.
        
        Args:
            image: BGR image from OpenCV
            
        Returns:
            torch.Tensor: Preprocessed tensor [1, 3, H, W]
        """
        # Convert BGR to RGB
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Normalize to [0, 1]
        image_norm = image_rgb.astype(np.float32) / 255.0
        
        # Convert to tensor [H, W, C] -> [C, H, W]
        image_tensor = torch.from_numpy(image_norm).permute(2, 0, 1)
        
        # Add batch dimension [1, C, H, W]
        image_tensor = image_tensor.unsqueeze(0)
        
        return image_tensor.to(self.device)
    
    def _postprocess(self, tensor):
        """
        Postprocess model output to image.
        
        Args:
            tensor: Model output tensor [1, 3, H, W]
            
        Returns:
            np.ndarray: BGR image for OpenCV
        """
        # Remove batch dimension and move to CPU
        image = tensor.squeeze(0).cpu().detach().numpy()
        
        # Convert [C, H, W] -> [H, W, C]
        image = image.transpose(1, 2, 0)
        
        # Clip to [0, 1] and convert to [0, 255]
        image = np.clip(image, 0, 1)
        image = (image * 255).astype(np.uint8)
        
        # Convert RGB to BGR
        image_bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        
        return image_bgr
    
    def enhance_frame(self, frame_path):
        """
        Enhance a single frame.
        
        Args:
            frame_path (str): Path to input frame
            
        Returns:
            str: Path to enhanced frame
        """
        # Read frame
        frame = cv2.imread(frame_path)
        
        if frame is None:
            raise ValueError(f"Cannot read frame: {frame_path}")
        
        # Preprocess
        input_tensor = self._preprocess(frame)
        
        # Inference
        with torch.no_grad():
            output_tensor = self.model(input_tensor)
        
        # Postprocess
        enhanced_frame = self._postprocess(output_tensor)
        
        # Save enhanced frame with same filename
        frame_name = Path(frame_path).name
        output_path = self.output_dir / frame_name
        cv2.imwrite(str(output_path), enhanced_frame)
        
        return str(output_path)
    
    def enhance_frames(self, frame_paths):
        """
        Enhance multiple frames.
        
        Args:
            frame_paths (list): List of frame paths
            
        Returns:
            list: List of enhanced frame paths
        """
        enhanced_paths = []
        
        print(f"\nEnhancing {len(frame_paths)} frames...")
        
        for frame_path in tqdm(frame_paths, desc="Enhancing frames"):
            try:
                enhanced_path = self.enhance_frame(frame_path)
                enhanced_paths.append(enhanced_path)
            except Exception as e:
                print(f"Error enhancing {frame_path}: {e}")
                continue
        
        print(f"✓ Enhanced {len(enhanced_paths)} frames -> {self.output_dir}")
        
        return enhanced_paths


def enhance_all_frames(frame_dir, model_path, output_dir="results/enhanced_frames", device='cuda'):
    """
    Convenience function to enhance all frames in a directory.
    
    Args:
        frame_dir (str): Directory containing raw frames
        model_path (str): Path to model weights
        output_dir (str): Directory to save enhanced frames
        device (str): 'cuda' or 'cpu'
        
    Returns:
        list: List of enhanced frame paths
    """
    # Get all frame paths
    frame_dir = Path(frame_dir)
    frame_paths = sorted(frame_dir.glob("*.png"))
    frame_paths = [str(p) for p in frame_paths]
    
    if not frame_paths:
        print(f"No frames found in {frame_dir}")
        return []
    
    # Create enhancer and process
    enhancer = FrameEnhancer(model_path, output_dir, device)
    return enhancer.enhance_frames(frame_paths)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python process_frames.py <frame_dir> <model_path> [output_dir] [device]")
        print("Example: python process_frames.py results/raw_frames weights/gopro_best.pth results/enhanced_frames cuda")
        sys.exit(1)
    
    frame_dir = sys.argv[1]
    model_path = sys.argv[2]
    output_dir = sys.argv[3] if len(sys.argv) > 3 else "results/enhanced_frames"
    device = sys.argv[4] if len(sys.argv) > 4 else 'cuda'
    
    enhanced_paths = enhance_all_frames(frame_dir, model_path, output_dir, device)
    print(f"Enhanced {len(enhanced_paths)} frames")
