"""
ROI-Based Damage Detector - Heuristic Analysis
===============================================

Detects damage in window and door ROIs using computer vision heuristics:
- Crack detection
- Glass breakage detection
- Structural deformation detection

Optimized for ROI crops (not full frames).

Author: Railway Wagon Inspection System
Date: January 4, 2026
"""

import cv2
import numpy as np
from typing import Dict, List, Tuple


class ROIDamageDetector:
    """Detect damage in cropped window/door ROIs using heuristics."""
    
    def __init__(self, sensitivity: str = 'medium', require_train_context: bool = True):
        """
        Initialize damage detector.
        
        Args:
            sensitivity: 'low', 'medium', or 'high'
            require_train_context: If True, validates ROI is on a train before damage detection
        """
        self.sensitivity = sensitivity
        self.require_train_context = require_train_context
        self.thresholds = self._get_thresholds(sensitivity)
        print(f"[ROI Damage Detector] Initialized (sensitivity: {sensitivity}, train context: {require_train_context})")
    
    def _get_thresholds(self, sensitivity: str) -> Dict:
        """Get detection thresholds based on sensitivity."""
        thresholds = {
            'low': {
                'crack_variance': 150,
                'glass_laplacian': 40,
                'deformation_circularity': 0.25,
                'min_damage_area': 1000
            },
            'medium': {
                'crack_variance': 100,
                'glass_laplacian': 30,
                'deformation_circularity': 0.30,
                'min_damage_area': 500
            },
            'high': {
                'crack_variance': 50,
                'glass_laplacian': 20,
                'deformation_circularity': 0.35,
                'min_damage_area': 200
            }
        }
        return thresholds.get(sensitivity, thresholds['medium'])
    
    def analyze_damage(self, roi_crop: np.ndarray, roi_class: str, full_frame: np.ndarray = None, bbox: tuple = None) -> Dict:
        """
        Analyze ROI for damage.
        
        Args:
            roi_crop: Cropped ROI image
            roi_class: 'window' or 'door'
            full_frame: Full frame image (optional, for train context validation)
            bbox: ROI bounding box (x, y, w, h) in full frame (optional)
            
        Returns:
            {
                'has_damage': bool,
                'damage_type': str or None,
                'confidence': float,
                'damage_score': float,
                'details': dict,
                'validation': dict  # Train context validation info
            }
        """
        if roi_crop is None or roi_crop.size == 0:
            return self._empty_result()
        
        # VALIDATION: Check if ROI is likely on a train (not background)
        if self.require_train_context and full_frame is not None and bbox is not None:
            is_train_roi = self._validate_train_context(roi_crop, full_frame, bbox)
            if not is_train_roi:
                print(f"[ROI DAMAGE] Skipping - ROI appears to be background, not train")
                result = self._empty_result()
                result['validation'] = {'is_train_roi': False, 'reason': 'background_detected'}
                return result
        
        # Run all detection methods
        crack_result = self._detect_cracks(roi_crop)
        glass_result = self._detect_glass_damage(roi_crop)
        deform_result = self._detect_deformation(roi_crop)
        
        # Aggregate results
        damage_scores = {
            'crack': crack_result['score'],
            'glass_damage': glass_result['score'],
            'deformation': deform_result['score']
        }
        
        # Find highest scoring damage type
        max_damage_type = max(damage_scores, key=damage_scores.get)
        max_score = damage_scores[max_damage_type]
        
        # Determine if damage exists (threshold-based)
        has_damage = max_score > 0.4  # 40% confidence threshold
        
        # Calculate overall confidence
        confidence = min(max_score, 1.0)
        
        return {
            'has_damage': has_damage,
            'damage_type': max_damage_type if has_damage else None,
            'confidence': confidence,
            'damage_score': max_score,
            'details': {
                'crack': crack_result,
                'glass_damage': glass_result,
                'deformation': deform_result
            },
            'validation': {'is_train_roi': True, 'reason': 'validated'}
        }
    
    def _detect_cracks(self, roi: np.ndarray) -> Dict:
        """
        Detect cracks using edge detection.
        
        Strategy:
        - Look for thin, elongated edge patterns
        - High edge density in linear formations
        """
        # Convert to grayscale
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        
        # Denoise
        denoised = cv2.bilateralFilter(gray, 5, 50, 50)
        
        # Detect edges
        edges = cv2.Canny(denoised, 50, 150)
        
        # Morphological operations to connect crack segments
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        dilated = cv2.dilate(edges, kernel, iterations=1)
        
        # Find contours
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        crack_score = 0.0
        crack_count = 0
        
        for contour in contours:
            area = cv2.contourArea(contour)
            
            if area < 100:  # Too small
                continue
            
            # Get bounding rectangle
            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = max(w, h) / (min(w, h) + 1e-6)
            
            # Cracks are elongated (high aspect ratio)
            if aspect_ratio > 3.0 and area > self.thresholds['min_damage_area'] / 2:
                crack_count += 1
                # Score based on area and elongation
                crack_score += min(0.3, area / 10000.0)
        
        # Normalize score
        final_score = min(crack_score, 1.0)
        
        return {
            'score': final_score,
            'count': crack_count,
            'detected': final_score > 0.3
        }
    
    def _detect_glass_damage(self, roi: np.ndarray) -> Dict:
        """
        Detect broken/shattered glass.
        
        Strategy:
        - Look for high texture variance
        - Detect sharp intensity gradients (glass fragments)
        """
        # Convert to grayscale
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        
        # Calculate Laplacian variance (sharpness measure)
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        laplacian_var = laplacian.var()
        
        # High variance indicates shattered glass
        glass_threshold = self.thresholds['glass_laplacian']
        
        if laplacian_var > glass_threshold * 2:
            score = 0.9
        elif laplacian_var > glass_threshold:
            score = 0.6
        else:
            score = min(laplacian_var / glass_threshold, 0.4)
        
        # Additional check: detect irregular bright spots (glass shards reflecting light)
        _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
        bright_spots = cv2.countNonZero(thresh)
        bright_ratio = bright_spots / gray.size
        
        # If many bright spots, likely shattered glass
        if bright_ratio > 0.15:
            score = max(score, 0.7)
        
        return {
            'score': min(score, 1.0),
            'laplacian_variance': laplacian_var,
            'bright_spot_ratio': bright_ratio,
            'detected': score > 0.4
        }
    
    def _detect_deformation(self, roi: np.ndarray) -> Dict:
        """
        Detect structural deformation.
        
        Strategy:
        - Look for irregular shapes and warped edges
        - Detect non-rectangular contours
        """
        # Convert to grayscale
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        
        # Apply adaptive thresholding
        adaptive = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                        cv2.THRESH_BINARY_INV, 11, 2)
        
        # Find contours
        contours, _ = cv2.findContours(adaptive, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        deform_score = 0.0
        irregular_count = 0
        
        for contour in contours:
            area = cv2.contourArea(contour)
            
            if area < self.thresholds['min_damage_area']:
                continue
            
            # Calculate circularity (measure of irregularity)
            perimeter = cv2.arcLength(contour, True)
            if perimeter == 0:
                continue
            
            circularity = 4 * np.pi * area / (perimeter * perimeter)
            
            # Low circularity = irregular shape = possible deformation
            if circularity < self.thresholds['deformation_circularity']:
                irregular_count += 1
                deform_score += (1 - circularity) * 0.4
        
        # Normalize
        final_score = min(deform_score, 1.0)
        
        return {
            'score': final_score,
            'irregular_shapes': irregular_count,
            'detected': final_score > 0.35
        }
    
    def _validate_train_context(self, roi_crop: np.ndarray, full_frame: np.ndarray, bbox: tuple) -> bool:
        """
        Validate that ROI is actually on a train, not background.
        
        Uses spatial analysis and color/texture features to determine if the ROI
        is part of a train wagon or a background object.
        
        Args:
            roi_crop: The cropped ROI image
            full_frame: Full frame image
            bbox: (x, y, w, h) of ROI in full frame
            
        Returns:
            True if ROI appears to be on a train, False if background
        """
        try:
            x, y, w, h = bbox
            frame_h, frame_w = full_frame.shape[:2]
            
            # Check 1: Vertical position - Trains are typically in lower 60% of frame
            roi_center_y = y + h/2
            y_ratio = roi_center_y / frame_h
            
            if y_ratio < 0.25:  # ROI in top 25% - likely sky/overhead structures
                print(f"  [VALIDATION] Rejected - too high in frame (y_ratio={y_ratio:.2f})")
                return False
            
            # Check 2: Size validation - Background objects have different size characteristics
            roi_area = w * h
            frame_area = frame_w * frame_h
            size_ratio = roi_area / frame_area
            
            if size_ratio > 0.5:  # Unreasonably large (>50% of frame)
                print(f"  [VALIDATION] Rejected - too large (size_ratio={size_ratio:.2f})")
                return False
            
            if size_ratio < 0.001:  # Too small (<0.1% of frame) - likely noise
                print(f"  [VALIDATION] Rejected - too small (size_ratio={size_ratio:.2f})")
                return False
            
            # Check 3: Train color signature analysis
            # Trains have distinct colors (painted wagons), background is more varied
            hsv_roi = cv2.cvtColor(roi_crop, cv2.COLOR_BGR2HSV)
            
            # Check hue consistency - trains have consistent colors
            hue_std = np.std(hsv_roi[:, :, 0])
            
            # Check saturation - trains are usually more saturated than gray backgrounds
            sat_mean = np.mean(hsv_roi[:, :, 1])
            
            # Check 4: Edge density - Trains have moderate edge density (windows, panels)
            # Background clutter has very high edge density
            gray_roi = cv2.cvtColor(roi_crop, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray_roi, 50, 150)
            edge_density = np.sum(edges > 0) / edges.size
            
            # Background objects (poles, buildings) have very high edge density (>15%)
            # Train windows have moderate edge density (3-12%)
            if edge_density > 0.20:  # Too much edge detail - likely background clutter
                print(f"  [VALIDATION] Rejected - excessive edges (density={edge_density:.3f})")
                return False
            
            # Check 5: Context expansion - Check surroundings
            # Expand ROI by 30% in each direction and check for train-like features
            expand_factor = 0.3
            ex = max(0, int(x - w * expand_factor))
            ey = max(0, int(y - h * expand_factor))
            ew = int(w * (1 + 2 * expand_factor))
            eh = int(h * (1 + 2 * expand_factor))
            
            # Clip to frame boundaries
            ex2 = min(frame_w, ex + ew)
            ey2 = min(frame_h, ey + eh)
            
            context_region = full_frame[ey:ey2, ex:ex2]
            
            # Check for horizontal lines in context (train wagons have strong horizontals)
            gray_context = cv2.cvtColor(context_region, cv2.COLOR_BGR2GRAY)
            edges_context = cv2.Canny(gray_context, 50, 150)
            lines = cv2.HoughLinesP(edges_context, 1, np.pi/180, threshold=50,
                                   minLineLength=int(ew*0.15), maxLineGap=10)
            
            horizontal_lines = 0
            if lines is not None:
                for line in lines:
                    x1, y1, x2, y2 = line[0]
                    angle = abs(np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi)
                    if angle < 30 or angle > 150:  # Horizontal
                        horizontal_lines += 1
            
            # Trains should have some horizontal structure
            has_horizontal_structure = horizontal_lines >= 2
            
            # Decision logic
            is_train = True
            reasons = []
            
            # Must have some horizontal structure (train characteristic)
            if not has_horizontal_structure:
                is_train = False
                reasons.append(f"no_horizontal_lines({horizontal_lines})")
            
            # Color characteristics should match train
            if hue_std > 50:  # Very inconsistent colors - likely background
                is_train = False
                reasons.append(f"inconsistent_color(std={hue_std:.1f})")
            
            if is_train:
                print(f"  [VALIDATION] ✓ Accepted as train ROI (y={y_ratio:.2f}, edges={edge_density:.3f}, h_lines={horizontal_lines})")
            else:
                print(f"  [VALIDATION] ✗ Rejected as background: {', '.join(reasons)}")
            
            return is_train
            
        except Exception as e:
            print(f"  [VALIDATION] Error in train context validation: {e}")
            # On error, be conservative and accept (avoid false rejections)
            return True
    
    def _empty_result(self) -> Dict:
        """Return empty result for invalid input."""
        return {
            'has_damage': False,
            'damage_type': None,
            'confidence': 0.0,
            'damage_score': 0.0,
            'details': {},
            'validation': {'is_train_roi': False, 'reason': 'invalid_input'}
        }
    
    def annotate_damage(self, roi: np.ndarray, damage_result: Dict) -> np.ndarray:
        """
        Annotate ROI with damage indicators.
        
        Args:
            roi: Original ROI image
            damage_result: Result from analyze_damage()
            
        Returns:
            Annotated ROI
        """
        annotated = roi.copy()
        
        if not damage_result['has_damage']:
            # Add "OK" label
            cv2.putText(annotated, "OK", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
            return annotated
        
        # Add damage indicator
        damage_type = damage_result['damage_type']
        confidence = damage_result['confidence']
        
        # Color code by damage type
        colors = {
            'crack': (0, 0, 255),           # Red
            'glass_damage': (0, 165, 255),  # Orange
            'deformation': (0, 255, 255)    # Yellow
        }
        color = colors.get(damage_type, (255, 0, 255))
        
        # Add border
        cv2.rectangle(annotated, (0, 0), (annotated.shape[1]-1, annotated.shape[0]-1),
                     color, 4)
        
        # Add label
        label = f"{damage_type.upper()}: {confidence*100:.0f}%"
        cv2.putText(annotated, label, (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        
        return annotated


def test_roi_damage_detector():
    """Test damage detector on sample ROI crops."""
    import sys
    from pathlib import Path
    
    if len(sys.argv) < 2:
        print("Usage: python roi_damage_detector.py <roi_image_path>")
        return
    
    image_path = sys.argv[1]
    roi = cv2.imread(image_path)
    
    if roi is None:
        print(f"Error: Could not load image from {image_path}")
        return
    
    # Initialize detector
    detector = ROIDamageDetector(sensitivity='medium')
    
    # Analyze damage
    result = detector.analyze_damage(roi, 'window')
    
    print(f"\nDamage Analysis Results:")
    print(f"  Has Damage: {result['has_damage']}")
    print(f"  Damage Type: {result['damage_type']}")
    print(f"  Confidence: {result['confidence']:.2%}")
    print(f"  Damage Score: {result['damage_score']:.2f}")
    
    print(f"\nDetailed Scores:")
    for damage_type, details in result['details'].items():
        print(f"  {damage_type}: {details['score']:.2f} (detected: {details.get('detected', False)})")
    
    # Annotate ROI
    annotated = detector.annotate_damage(roi, result)
    
    # Save results
    output_dir = Path('damage_analysis_results')
    output_dir.mkdir(exist_ok=True)
    
    output_path = output_dir / f"{Path(image_path).stem}_damage_analysis.jpg"
    cv2.imwrite(str(output_path), annotated)
    
    print(f"\nAnnotated image saved to: {output_path}")


if __name__ == '__main__':
    test_roi_damage_detector()
