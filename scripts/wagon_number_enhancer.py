"""
Aggressive Wagon Number Enhancement for Sharp OCR
==================================================
Focuses specifically on wagon number regions with multi-stage enhancement.

PIPELINE:
1. Precise wagon number region detection (adaptive)
2. Super-resolution upscaling (2x-4x)
3. Aggressive CLAHE contrast enhancement
4. Bilateral filtering (preserve edges, reduce noise)
5. Adaptive thresholding for text isolation
6. Morphological operations (text refinement)
7. Strong sharpening for OCR clarity

Author: Railway Wagon Inspection System
Date: January 8, 2026
"""

import cv2
import numpy as np
from pathlib import Path
from tqdm import tqdm


class WagonNumberEnhancer:
    """Aggressive enhancement specifically for wagon numbers."""
    
    def __init__(self, output_dir, upscale_factor=3, clahe_clip=4.0,
                 bilateral_d=9, sharpen_strength=1.5):
        """
        Initialize aggressive wagon number enhancer.
        
        Args:
            output_dir (str): Directory to save enhanced images
            upscale_factor (int): Super-resolution scale (2-4 recommended)
            clahe_clip (float): CLAHE clip limit (3.0-5.0 for aggressive)
            bilateral_d (int): Bilateral filter diameter
            sharpen_strength (float): Sharpening strength (1.0-2.0)
        """
        self.output_dir = Path(output_dir)
        self.upscale_factor = upscale_factor
        self.clahe_clip = clahe_clip
        self.bilateral_d = bilateral_d
        self.sharpen_strength = sharpen_strength
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # CLAHE for aggressive contrast
        self.clahe = cv2.createCLAHE(clipLimit=clahe_clip, tileGridSize=(4, 4))
        
        print(f"Aggressive Wagon Number Enhancer initialized:")
        print(f"  - Upscaling: {upscale_factor}x")
        print(f"  - CLAHE clip: {clahe_clip} (aggressive)")
        print(f"  - Bilateral filter: {bilateral_d}px")
        print(f"  - Sharpen: {sharpen_strength} (strong)")
        print(f"  - Output: {self.output_dir}")
    
    def detect_text_region(self, image):
        """
        Detect the precise text region using edge detection and contours.
        
        Args:
            image (np.ndarray): Input image
            
        Returns:
            tuple: (x, y, w, h) of detected text region, or None if not found
        """
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Edge detection
        edges = cv2.Canny(blurred, 30, 150)
        
        # Dilate edges to connect text components
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (20, 5))
        dilated = cv2.dilate(edges, kernel, iterations=2)
        
        # Find contours
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return None
        
        # Filter contours by aspect ratio (wagon numbers are typically wide)
        valid_contours = []
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            aspect_ratio = w / h if h > 0 else 0
            area = w * h
            
            # Wagon numbers: wide aspect ratio, reasonable size
            if 2.0 < aspect_ratio < 15.0 and area > 500:
                valid_contours.append((x, y, w, h, area))
        
        if not valid_contours:
            return None
        
        # Get largest valid contour
        valid_contours.sort(key=lambda x: x[4], reverse=True)
        x, y, w, h, _ = valid_contours[0]
        
        # Add padding
        padding = 10
        h_img, w_img = image.shape[:2]
        x = max(0, x - padding)
        y = max(0, y - padding)
        w = min(w_img - x, w + 2 * padding)
        h = min(h_img - y, h + 2 * padding)
        
        return (x, y, w, h)
    
    def enhance_wagon_number(self, image_path, detect_region=True):
        """
        Apply aggressive multi-stage enhancement for wagon numbers.
        
        Args:
            image_path (str): Path to input image
            detect_region (bool): Auto-detect text region if True
            
        Returns:
            tuple: (enhanced_path, binary_path, debug_path)
        """
        # Read image
        image = cv2.imread(image_path)
        
        if image is None:
            raise ValueError(f"Cannot read image: {image_path}")
        
        original = image.copy()
        
        # STAGE 1: Detect and crop to text region (optional but recommended)
        if detect_region:
            text_box = self.detect_text_region(image)
            if text_box:
                x, y, w, h = text_box
                image = image[y:y+h, x:x+w]
                print(f"  Detected text region: {w}x{h} at ({x}, {y})")
        
        # STAGE 2: Super-resolution upscaling
        if self.upscale_factor > 1:
            new_width = image.shape[1] * self.upscale_factor
            new_height = image.shape[0] * self.upscale_factor
            image = cv2.resize(image, (new_width, new_height), 
                              interpolation=cv2.INTER_CUBIC)
        
        # STAGE 3: Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # STAGE 4: Bilateral filtering (edge-preserving denoising)
        denoised = cv2.bilateralFilter(gray, self.bilateral_d, 75, 75)
        
        # STAGE 5: Aggressive CLAHE
        clahe_enhanced = self.clahe.apply(denoised)
        
        # STAGE 6: Strong sharpening
        sharpened = self._aggressive_sharpen(clahe_enhanced)
        
        # STAGE 7: Adaptive thresholding for binary text
        binary = cv2.adaptiveThreshold(
            sharpened, 255, 
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 
            blockSize=11, 
            C=2
        )
        
        # STAGE 8: Morphological operations to clean text
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
        
        # Save outputs
        image_name = Path(image_path).stem
        
        enhanced_path = self.output_dir / f"{image_name}_enhanced.png"
        binary_path = self.output_dir / f"{image_name}_binary.png"
        debug_path = self.output_dir / f"{image_name}_debug.png"
        
        # Save enhanced grayscale
        cv2.imwrite(str(enhanced_path), sharpened)
        
        # Save binary (best for OCR)
        cv2.imwrite(str(binary_path), binary)
        
        # Save debug visualization (side-by-side comparison)
        debug_vis = self._create_debug_visualization(original, sharpened, binary)
        cv2.imwrite(str(debug_path), debug_vis)
        
        return str(enhanced_path), str(binary_path), str(debug_path)
    
    def _aggressive_sharpen(self, image):
        """
        Apply strong sharpening using unsharp mask.
        
        Args:
            image (np.ndarray): Input image
            
        Returns:
            np.ndarray: Sharpened image
        """
        # Gaussian blur
        blurred = cv2.GaussianBlur(image, (0, 0), 2)
        
        # Strong unsharp mask
        sharpened = cv2.addWeighted(image, 1 + self.sharpen_strength, 
                                    blurred, -self.sharpen_strength, 0)
        
        # Apply Laplacian sharpening as well
        laplacian = cv2.Laplacian(image, cv2.CV_64F)
        sharpened = cv2.convertScaleAbs(sharpened - 0.5 * laplacian)
        
        return sharpened
    
    def _create_debug_visualization(self, original, enhanced, binary):
        """Create side-by-side comparison for debugging."""
        # Resize all to same height
        h = 400
        
        # Resize original
        aspect = original.shape[1] / original.shape[0]
        w_orig = int(h * aspect)
        orig_resized = cv2.resize(original, (w_orig, h))
        
        # Resize enhanced
        aspect = enhanced.shape[1] / enhanced.shape[0]
        w_enh = int(h * aspect)
        enh_resized = cv2.resize(enhanced, (w_enh, h))
        enh_color = cv2.cvtColor(enh_resized, cv2.COLOR_GRAY2BGR)
        
        # Resize binary
        bin_resized = cv2.resize(binary, (w_enh, h))
        bin_color = cv2.cvtColor(bin_resized, cv2.COLOR_GRAY2BGR)
        
        # Add labels
        cv2.putText(orig_resized, "Original", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(enh_color, "Enhanced", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(bin_color, "Binary (OCR)", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        # Concatenate horizontally
        combined = np.hstack([orig_resized, enh_color, bin_color])
        
        return combined
    
    def process_batch(self, image_paths, detect_region=True):
        """
        Process multiple images with aggressive enhancement.
        
        Args:
            image_paths (list): List of image paths
            detect_region (bool): Auto-detect text regions
            
        Returns:
            tuple: (enhanced_paths, binary_paths, debug_paths)
        """
        enhanced_paths = []
        binary_paths = []
        debug_paths = []
        
        print(f"\nProcessing {len(image_paths)} images with aggressive enhancement...")
        
        for img_path in tqdm(image_paths, desc="Enhancing wagon numbers"):
            try:
                enh, binary, debug = self.enhance_wagon_number(img_path, detect_region)
                enhanced_paths.append(enh)
                binary_paths.append(binary)
                debug_paths.append(debug)
            except Exception as e:
                print(f"\nError processing {img_path}: {e}")
                continue
        
        print(f"✓ Enhanced {len(enhanced_paths)} images -> {self.output_dir}")
        
        return enhanced_paths, binary_paths, debug_paths


def enhance_wagon_numbers_sharp(input_dir, output_dir="wagon_number_enhanced",
                                upscale_factor=3, detect_region=True):
    """
    Convenience function for batch wagon number enhancement.
    
    Args:
        input_dir (str): Directory with wagon images
        output_dir (str): Output directory
        upscale_factor (int): Upscaling factor (2-4)
        detect_region (bool): Auto-detect text regions
        
    Returns:
        tuple: (enhanced_paths, binary_paths, debug_paths)
    """
    enhancer = WagonNumberEnhancer(
        output_dir=output_dir,
        upscale_factor=upscale_factor,
        clahe_clip=4.0,  # Aggressive
        bilateral_d=9,
        sharpen_strength=1.5  # Strong
    )
    
    # Get all images
    input_path = Path(input_dir)
    image_paths = sorted(input_path.glob("*.png")) + sorted(input_path.glob("*.jpg"))
    image_paths = [str(p) for p in image_paths]
    
    return enhancer.process_batch(image_paths, detect_region)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python wagon_number_enhancer.py <input_dir> [output_dir]")
        sys.exit(1)
    
    input_dir = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "wagon_enhanced"
    
    enhance_wagon_numbers_sharp(input_dir, output_dir)
