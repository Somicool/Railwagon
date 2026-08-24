"""
Text-Specific Enhancement Module
=================================
Applies OCR-optimized enhancement to fused band images.

APPROACH:
---------
1. Keep COLOR image (some OCR engines use color info)
2. Convert to LAB color space
3. Apply mild CLAHE on L channel only (contrast enhancement)
4. Recombine channels
5. Apply very mild sharpening
6. Convert to grayscale ONLY for OCR input

This preserves text structure without introducing artifacts.

Author: Railway Wagon Inspection System
Date: 2025-12-22
"""

import cv2
import numpy as np
from pathlib import Path
from tqdm import tqdm


class TextEnhancer:
    """Apply text-specific enhancement for OCR."""
    
    def __init__(self, output_dir, clahe_clip=2.0, clahe_grid=(8, 8), 
                 sharpen_strength=0.3):
        """
        Initialize text enhancer.
        
        Args:
            output_dir (str): Directory to save enhanced text images
            clahe_clip (float): CLAHE clip limit (2.0-3.0 recommended)
            clahe_grid (tuple): CLAHE grid size
            sharpen_strength (float): Sharpening strength (0.1-0.5)
        """
        self.output_dir = Path(output_dir)
        self.clahe_clip = clahe_clip
        self.clahe_grid = clahe_grid
        self.sharpen_strength = sharpen_strength
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create CLAHE object
        self.clahe = cv2.createCLAHE(clipLimit=clahe_clip, 
                                     tileGridSize=clahe_grid)
        
        print(f"Text Enhancer initialized:")
        print(f"  - CLAHE clip: {clahe_clip}")
        print(f"  - CLAHE grid: {clahe_grid}")
        print(f"  - Sharpen: {sharpen_strength}")
        print(f"  - Output: {self.output_dir}")
    
    def enhance_for_ocr(self, image_path):
        """
        Apply text-specific enhancement.
        
        Args:
            image_path (str): Path to fused band image
            
        Returns:
            tuple: (enhanced_color_path, enhanced_gray_path)
        """
        # Read image
        image = cv2.imread(image_path)
        
        if image is None:
            raise ValueError(f"Cannot read image: {image_path}")
        
        # Step 1: Convert BGR to LAB
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        
        # Step 2: Apply CLAHE to L channel only
        l, a, b = cv2.split(lab)
        l_clahe = self.clahe.apply(l)
        
        # Step 3: Merge channels back
        lab_enhanced = cv2.merge([l_clahe, a, b])
        
        # Step 4: Convert back to BGR
        enhanced_color = cv2.cvtColor(lab_enhanced, cv2.COLOR_LAB2BGR)
        
        # Step 5: Apply mild sharpening
        if self.sharpen_strength > 0:
            enhanced_color = self._sharpen(enhanced_color)
        
        # Step 6: Convert to grayscale for OCR
        enhanced_gray = cv2.cvtColor(enhanced_color, cv2.COLOR_BGR2GRAY)
        
        # Optional: Apply binary thresholding for very clear text
        # (can be helpful for some OCR engines)
        # enhanced_gray = cv2.adaptiveThreshold(
        #     enhanced_gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        #     cv2.THRESH_BINARY, 11, 2
        # )
        
        # Save both color and grayscale versions
        image_name = Path(image_path).stem
        
        color_output = self.output_dir / f"{image_name}_color.png"
        gray_output = self.output_dir / f"{image_name}_gray.png"
        
        cv2.imwrite(str(color_output), enhanced_color)
        cv2.imwrite(str(gray_output), enhanced_gray)
        
        return str(color_output), str(gray_output)
    
    def _sharpen(self, image):
        """
        Apply mild unsharp masking.
        
        Args:
            image (np.ndarray): Input image
            
        Returns:
            np.ndarray: Sharpened image
        """
        # Gaussian blur
        blurred = cv2.GaussianBlur(image, (0, 0), 3)
        
        # Unsharp mask: image + strength * (image - blurred)
        sharpened = cv2.addWeighted(image, 1 + self.sharpen_strength, 
                                    blurred, -self.sharpen_strength, 0)
        
        return sharpened
    
    def enhance_all(self, fused_paths):
        """
        Enhance all fused images for OCR.
        
        Args:
            fused_paths (list): List of fused image paths
            
        Returns:
            tuple: (color_paths, gray_paths)
        """
        color_paths = []
        gray_paths = []
        
        print(f"\nEnhancing {len(fused_paths)} images for OCR...")
        
        for fused_path in tqdm(fused_paths, desc="Text enhancement"):
            try:
                color_path, gray_path = self.enhance_for_ocr(fused_path)
                color_paths.append(color_path)
                gray_paths.append(gray_path)
            except Exception as e:
                print(f"Error enhancing {fused_path}: {e}")
                continue
        
        print(f"✓ Enhanced {len(gray_paths)} images -> {self.output_dir}")
        
        return color_paths, gray_paths


def enhance_for_text_ocr(fused_dir, output_dir="results/enhanced_text",
                         clahe_clip=2.0, sharpen_strength=0.3):
    """
    Convenience function for text enhancement.
    
    Args:
        fused_dir (str): Directory containing fused images
        output_dir (str): Directory to save enhanced images
        clahe_clip (float): CLAHE clip limit
        sharpen_strength (float): Sharpening strength
        
    Returns:
        tuple: (color_paths, gray_paths)
    """
    # Get all fused paths
    fused_dir = Path(fused_dir)
    fused_paths = sorted(fused_dir.glob("*.png"))
    fused_paths = [str(p) for p in fused_paths]
    
    if not fused_paths:
        print(f"No fused images found in {fused_dir}")
        return [], []
    
    # Create enhancer
    enhancer = TextEnhancer(output_dir, clahe_clip=clahe_clip, 
                           sharpen_strength=sharpen_strength)
    return enhancer.enhance_all(fused_paths)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python text_enhancement.py <fused_dir> [output_dir] [clahe_clip] [sharpen]")
        print("Example: python text_enhancement.py results/fused results/enhanced_text 2.0 0.3")
        sys.exit(1)
    
    fused_dir = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "results/enhanced_text"
    clahe_clip = float(sys.argv[3]) if len(sys.argv) > 3 else 2.0
    sharpen = float(sys.argv[4]) if len(sys.argv) > 4 else 0.3
    
    color_paths, gray_paths = enhance_for_text_ocr(
        fused_dir, output_dir, clahe_clip, sharpen
    )
    print(f"Enhanced {len(gray_paths)} images for OCR")
