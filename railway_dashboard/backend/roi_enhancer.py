"""
ROI Enhancement Module - Task-Specific Image Processing
========================================================

Applies different enhancement strategies based on ROI type:
- wagon_number: Aggressive text enhancement (sharpen + contrast + binarization)
- window/door: Mild structural enhancement (preserve edges + denoise)

Author: Railway Wagon Inspection System
Date: January 4, 2026
"""

import cv2
import numpy as np
from typing import Tuple


class ROIEnhancer:
    """Task-aware enhancement for different ROI types."""
    
    def __init__(self):
        """Initialize ROI enhancer."""
        print("[ROI Enhancer] Initialized with task-specific strategies")
    
    def enhance_roi(self, roi_image: np.ndarray, roi_class: str) -> np.ndarray:
        """
        Apply task-specific enhancement to ROI.
        
        Args:
            roi_image: Cropped ROI image
            roi_class: 'wagon_number', 'window', or 'door'
            
        Returns:
            Enhanced ROI image
        """
        if roi_image is None or roi_image.size == 0:
            return roi_image
        
        if roi_class == 'wagon_number':
            return self.enhance_for_ocr(roi_image)
        elif roi_class in ['window', 'door']:
            return self.enhance_for_damage(roi_image)
        else:
            # Unknown class, return original
            return roi_image
    
    def enhance_for_ocr(self, roi_image: np.ndarray) -> np.ndarray:
        """
        AGGRESSIVE enhancement for OCR.
        
        Strategy:
        1. Grayscale conversion
        2. Denoising
        3. Contrast enhancement (CLAHE)
        4. Sharpening
        5. Adaptive binarization
        
        Args:
            roi_image: Wagon number ROI
            
        Returns:
            OCR-optimized image
        """
        # Convert to grayscale if needed
        if len(roi_image.shape) == 3:
            gray = cv2.cvtColor(roi_image, cv2.COLOR_BGR2GRAY)
        else:
            gray = roi_image.copy()
        
        # Step 1: Denoise to remove camera noise
        denoised = cv2.fastNlMeansDenoising(gray, h=10)
        
        # Step 2: Contrast enhancement using CLAHE
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(denoised)
        
        # Step 3: Aggressive sharpening for text clarity
        kernel = np.array([[-1, -1, -1],
                          [-1,  9, -1],
                          [-1, -1, -1]])
        sharpened = cv2.filter2D(enhanced, -1, kernel)
        
        # Step 4: Adaptive thresholding for binarization
        # This creates high-contrast black/white text
        binary = cv2.adaptiveThreshold(
            sharpened, 
            255, 
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            blockSize=11,
            C=2
        )
        
        # Step 5: Morphological operations to connect broken text
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        morph = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=1)
        
        # Convert back to BGR for consistency
        result = cv2.cvtColor(morph, cv2.COLOR_GRAY2BGR)
        
        print(f"[OCR Enhancement] Applied aggressive text enhancement")
        return result
    
    def enhance_for_damage(self, roi_image: np.ndarray) -> np.ndarray:
        """
        MILD enhancement for damage detection.
        
        Strategy:
        1. Light denoising
        2. Edge preservation
        3. Slight contrast boost
        4. NO aggressive operations (preserve damage patterns)
        
        Args:
            roi_image: Window/door ROI
            
        Returns:
            Structure-preserved enhanced image
        """
        # Step 1: Bilateral filter - preserves edges while reducing noise
        denoised = cv2.bilateralFilter(roi_image, d=5, sigmaColor=50, sigmaSpace=50)
        
        # Step 2: Mild contrast enhancement
        lab = cv2.cvtColor(denoised, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        # Apply CLAHE with conservative settings
        clahe = cv2.createCLAHE(clipLimit=1.5, tileGridSize=(4, 4))
        l_enhanced = clahe.apply(l)
        
        # Merge back
        enhanced_lab = cv2.merge([l_enhanced, a, b])
        enhanced = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)
        
        # Step 3: Slight sharpening (very mild)
        kernel = np.array([[0, -0.5, 0],
                          [-0.5, 3, -0.5],
                          [0, -0.5, 0]])
        sharpened = cv2.filter2D(enhanced, -1, kernel)
        
        print(f"[Damage Enhancement] Applied mild structural enhancement")
        return sharpened
    
    def enhance_for_ocr_alternative(self, roi_image: np.ndarray) -> np.ndarray:
        """
        Alternative OCR enhancement using Otsu's binarization.
        Good for very poor quality text.
        
        Args:
            roi_image: Wagon number ROI
            
        Returns:
            Enhanced image
        """
        # Convert to grayscale
        if len(roi_image.shape) == 3:
            gray = cv2.cvtColor(roi_image, cv2.COLOR_BGR2GRAY)
        else:
            gray = roi_image.copy()
        
        # Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Otsu's thresholding
        _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Convert back to BGR
        result = cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)
        return result
    
    def enhance_for_damage_edge_focus(self, roi_image: np.ndarray) -> np.ndarray:
        """
        Alternative damage enhancement focusing on edge detection.
        Good for crack detection.
        
        Args:
            roi_image: Window/door ROI
            
        Returns:
            Edge-enhanced image
        """
        # Convert to grayscale
        gray = cv2.cvtColor(roi_image, cv2.COLOR_BGR2GRAY)
        
        # Bilateral filter
        denoised = cv2.bilateralFilter(gray, 9, 75, 75)
        
        # Enhance edges using Laplacian
        laplacian = cv2.Laplacian(denoised, cv2.CV_64F)
        laplacian = np.uint8(np.absolute(laplacian))
        
        # Combine with original
        alpha = 0.7
        enhanced = cv2.addWeighted(denoised, alpha, laplacian, 1 - alpha, 0)
        
        # Convert back to BGR
        result = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)
        return result


class GlobalEnhancer:
    """
    Optional light global enhancement applied before ROI detection.
    This is OPTIONAL and should be used sparingly.
    """
    
    def __init__(self):
        """Initialize global enhancer."""
        print("[Global Enhancer] Initialized (OPTIONAL - use lightly)")
    
    def enhance_frame(self, frame: np.ndarray, apply: bool = False) -> np.ndarray:
        """
        Apply OPTIONAL light global enhancement.
        
        Args:
            frame: Input video frame
            apply: If False, returns original frame (enhancement skipped)
            
        Returns:
            Enhanced frame (or original if apply=False)
        """
        if not apply:
            return frame
        
        if frame is None or frame.size == 0:
            return frame
        
        print("[Global Enhancement] Applying light frame enhancement")
        
        # Step 1: Light denoising
        denoised = cv2.fastNlMeansDenoisingColored(frame, h=3, hColor=3)
        
        # Step 2: Mild brightness/contrast adjustment
        alpha = 1.1  # Contrast (1.0-1.3 range)
        beta = 5     # Brightness (0-20 range)
        adjusted = cv2.convertScaleAbs(denoised, alpha=alpha, beta=beta)
        
        # Step 3: Minimal sharpening
        kernel = np.array([[0, -0.25, 0],
                          [-0.25, 2, -0.25],
                          [0, -0.25, 0]])
        enhanced = cv2.filter2D(adjusted, -1, kernel)
        
        return enhanced
    
    def enhance_low_light(self, frame: np.ndarray) -> np.ndarray:
        """
        Specific enhancement for low-light conditions.
        
        Args:
            frame: Input frame
            
        Returns:
            Brightness-corrected frame
        """
        # Convert to LAB color space
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        # Apply CLAHE to L channel
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l_enhanced = clahe.apply(l)
        
        # Merge and convert back
        enhanced_lab = cv2.merge([l_enhanced, a, b])
        enhanced = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)
        
        return enhanced


def test_roi_enhancer():
    """Test the ROI enhancer with sample crops."""
    import sys
    from pathlib import Path
    
    if len(sys.argv) < 3:
        print("Usage: python roi_enhancer.py <image_path> <roi_type>")
        print("  roi_type: 'wagon_number', 'window', or 'door'")
        return
    
    image_path = sys.argv[1]
    roi_type = sys.argv[2]
    
    image = cv2.imread(image_path)
    if image is None:
        print(f"Error: Could not load image from {image_path}")
        return
    
    # Initialize enhancer
    enhancer = ROIEnhancer()
    
    # Enhance ROI
    enhanced = enhancer.enhance_roi(image, roi_type)
    
    # Save results
    output_dir = Path('enhancement_results')
    output_dir.mkdir(exist_ok=True)
    
    original_path = output_dir / f"{roi_type}_original.jpg"
    enhanced_path = output_dir / f"{roi_type}_enhanced.jpg"
    
    cv2.imwrite(str(original_path), image)
    cv2.imwrite(str(enhanced_path), enhanced)
    
    print(f"\nEnhancement complete!")
    print(f"  Original: {original_path}")
    print(f"  Enhanced: {enhanced_path}")
    
    # Create comparison image
    comparison = np.hstack([image, enhanced])
    comparison_path = output_dir / f"{roi_type}_comparison.jpg"
    cv2.imwrite(str(comparison_path), comparison)
    print(f"  Comparison: {comparison_path}")


if __name__ == '__main__':
    test_roi_enhancer()
