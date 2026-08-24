"""
Wagon Damage Detection Module
==============================

Detects visible damage on railway wagon windows and doors.
Identifies cracks, broken glass, damaged frames, and structural issues.

Author: Railway Wagon Inspection System
Date: January 4, 2026
"""

import cv2
import numpy as np
from pathlib import Path
import torch


class WagonDamageDetector:
    """Detect damage on wagon windows and doors using computer vision."""
    
    def __init__(self, device='cpu', min_train_coverage=0.15):
        """Initialize damage detector.
        
        Args:
            device: 'cpu' or 'cuda' for GPU acceleration
            min_train_coverage: Minimum percentage of frame that should contain train/wagon
                               (0.15 = 15% of frame) to run damage detection
        """
        self.device = device
        self.min_train_coverage = min_train_coverage
        print(f"Wagon Damage Detector initialized (Device: {device}, Min Coverage: {min_train_coverage*100}%)")
    
    def detect_damage(self, image):
        """
        Detect damage on wagon windows and doors.
        
        Args:
            image: Input image (BGR format, numpy array)
            
        Returns:
            dict: {
                'has_damage': bool,
                'damage_type': str or None,
                'confidence': float,
                'damage_count': int,
                'locations': list of (x, y, w, h),
                'annotated_image': numpy array with damage marked
            }
        """
        if image is None or image.size == 0:
            return self._empty_result()
        
        # Create a copy for annotation
        annotated = image.copy()
        h, w = image.shape[:2]
        
        # FIRST: Check if there's actually a train/wagon in the frame
        # This prevents false detections from background objects
        has_train, train_coverage = self._detect_train_presence(image)
        if not has_train:
            print(f"[DAMAGE DETECTOR] No significant train detected ({train_coverage*100:.1f}% < {self.min_train_coverage*100}%) - skipping damage detection")
            return {
                'has_damage': False,
                'damage_type': None,
                'damage_types': [],
                'confidence': 0.0,
                'damage_count': 0,
                'locations': [],
                'annotated_image': annotated,
                'train_coverage': train_coverage
            }
        
        print(f"[DAMAGE DETECTOR] Train detected ({train_coverage*100:.1f}% coverage) - proceeding with damage detection")
        
        # Detect window/door regions first - REQUIRED for damage detection
        regions = self._detect_window_door_regions(image)
        if not regions:
            # No windows/doors detected - NO DAMAGE DETECTION
            print("[DAMAGE DETECTOR] No window/door regions found - skipping damage detection")
            return {
                'has_damage': False,
                'damage_type': None,
                'damage_types': [],
                'confidence': 0.0,
                'damage_count': 0,
                'locations': [],
                'annotated_image': annotated,
                'train_coverage': train_coverage
            }
        
        # Strategy: Use multiple detection methods and combine results
        damages = []
        
        # Analyze each region for damage
        for region in regions:
            rx, ry, rw, rh = region['bbox']
            roi = image[ry:ry+rh, rx:rx+rw]
            
            # Method 1: Detect cracks using edge detection and morphology
            crack_damages = self._detect_cracks(roi)
            # Adjust coordinates to full image
            for crack in crack_damages:
                cx, cy, cw, ch = crack['bbox']
                crack['bbox'] = (rx + cx, ry + cy, cw, ch)
            damages.extend(crack_damages)
            
            # Method 2: Detect broken/shattered glass using texture analysis
            glass_damages = self._detect_broken_glass(roi)
            # Adjust coordinates to full image
            for glass in glass_damages:
                gx, gy, gw, gh = glass['bbox']
                glass['bbox'] = (rx + gx, ry + gy, gw, gh)
            damages.extend(glass_damages)
            
            # Method 3: Detect structural damage using contour irregularities
            structural_damages = self._detect_structural_damage(roi)
            # Adjust coordinates to full image
            for structural in structural_damages:
                sx, sy, sw, sh = structural['bbox']
                structural['bbox'] = (rx + sx, ry + sy, sw, sh)
            damages.extend(structural_damages)
        
        # Filter and deduplicate damages (STRICT: reduce false positives)
        damages = self._filter_damages(damages, min_confidence=0.6)
        
        # Annotate image with detected damages
        for damage in damages:
            x, y, w, h = damage['bbox']
            damage_type = damage['type']
            confidence = damage['confidence']
            
            # Color code by damage type
            if damage_type == 'crack':
                color = (0, 0, 255)  # Red
                label = 'CRACK'
            elif damage_type == 'broken_glass':
                color = (0, 165, 255)  # Orange
                label = 'BROKEN GLASS'
            elif damage_type == 'structural':
                color = (0, 255, 255)  # Yellow
                label = 'STRUCTURAL DAMAGE'
            else:
                color = (255, 0, 255)  # Magenta
                label = 'DAMAGE'
            
            # Draw bounding box
            cv2.rectangle(annotated, (x, y), (x + w, y + h), color, 3)
            
            # Add label with confidence
            label_text = f"{label} ({confidence*100:.0f}%)"
            label_size = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
            cv2.rectangle(annotated, (x, y - label_size[1] - 10), 
                         (x + label_size[0], y), color, -1)
            cv2.putText(annotated, label_text, (x, y - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Determine overall result
        has_damage = len(damages) > 0
        damage_types = list(set([d['type'] for d in damages]))
        
        # Primary damage type (most confident)
        if damages:
            primary_damage = max(damages, key=lambda x: x['confidence'])
            damage_type = primary_damage['type']
            avg_confidence = np.mean([d['confidence'] for d in damages])
        else:
            damage_type = None
            avg_confidence = 0.0
        
        return {
            'has_damage': has_damage,
            'damage_type': damage_type,
            'damage_types': damage_types,
            'confidence': float(avg_confidence),
            'damage_count': len(damages),
            'damages': damages,
            'annotated_image': annotated,
            'train_coverage': train_coverage
        }
    
    def _detect_cracks(self, image):
        """Detect cracks using edge detection and morphological operations."""
        damages = []
        
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply bilateral filter to reduce noise while keeping edges
            denoised = cv2.bilateralFilter(gray, 9, 75, 75)
            
            # Enhance contrast
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(denoised)
            
            # Detect edges using Canny
            edges = cv2.Canny(enhanced, 50, 150)
            
            # Morphological operations to connect broken crack segments
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            dilated = cv2.dilate(edges, kernel, iterations=1)
            
            # Find contours
            contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                
                # Filter small noise
                if area < 100:
                    continue
                
                # Get bounding box
                x, y, w, h = cv2.boundingRect(contour)
                
                # Cracks are typically thin and elongated
                aspect_ratio = max(w, h) / (min(w, h) + 1e-6)
                
                # Check if it looks like a crack (elongated) - EXTREMELY STRICT
                if aspect_ratio > 6.0 and area > 2000:  # Much stricter
                    # Calculate confidence based on characteristics
                    perimeter = cv2.arcLength(contour, True)
                    circularity = 4 * np.pi * area / (perimeter * perimeter + 1e-6)
                    
                    # Cracks have low circularity (irregular shape)
                    confidence = min(0.85, (1 - circularity) * 0.7 + 0.15)
                    
                    damages.append({
                        'type': 'crack',
                        'bbox': (x, y, w, h),
                        'confidence': confidence,
                        'area': area
                    })
        
        except Exception as e:
            print(f"Error in crack detection: {e}")
        
        return damages
    
    def _detect_broken_glass(self, image):
        """Detect broken/shattered glass using texture analysis."""
        damages = []
        
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Broken glass creates sharp intensity variations
            # Use Laplacian for detecting sharp changes
            laplacian = cv2.Laplacian(gray, cv2.CV_64F)
            laplacian = np.abs(laplacian).astype(np.uint8)
            
            # Threshold to find high-variance regions
            _, thresh = cv2.threshold(laplacian, 30, 255, cv2.THRESH_BINARY)
            
            # Morphological closing to connect fragments
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
            closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=2)
            
            # Find contours
            contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                
                # Broken glass creates moderate to large irregular regions - EXTREMELY STRICT
                if area < 5000 or area > image.shape[0] * image.shape[1] * 0.5:
                    continue
                
                x, y, w, h = cv2.boundingRect(contour)
                
                # Extract region
                roi_gray = gray[y:y+h, x:x+w]
                
                # Calculate texture variance (broken glass has high variance)
                variance = np.var(roi_gray)
                
                # Normalize variance to confidence score - EXTREMELY STRICT
                confidence = min(0.9, variance / 10000.0)
                
                if confidence > 0.90:
                    damages.append({
                        'type': 'broken_glass',
                        'bbox': (x, y, w, h),
                        'confidence': confidence,
                        'area': area
                    })
        
        except Exception as e:
            print(f"Error in broken glass detection: {e}")
        
        return damages
    
    def _detect_structural_damage(self, image):
        """Detect structural damage using contour irregularities."""
        damages = []
        
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply adaptive thresholding
            adaptive = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                            cv2.THRESH_BINARY_INV, 11, 2)
            
            # Find contours
            contours, _ = cv2.findContours(adaptive, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                
                # Filter by size - EXTREMELY STRICT
                if area < 1500 or area > image.shape[0] * image.shape[1] * 0.6:
                    continue
                
                # Get bounding box
                x, y, w, h = cv2.boundingRect(contour)
                
                # Calculate shape irregularity
                perimeter = cv2.arcLength(contour, True)
                if perimeter == 0:
                    continue
                
                circularity = 4 * np.pi * area / (perimeter * perimeter)
                
                # Structural damage creates very irregular shapes - EXTREMELY STRICT
                if circularity < 0.2:  # Very irregular
                    confidence = min(0.85, (1 - circularity) * 0.7)
                    
                    damages.append({
                        'type': 'structural',
                        'bbox': (x, y, w, h),
                        'confidence': confidence,
                        'area': area
                    })
        
        except Exception as e:
            print(f"Error in structural damage detection: {e}")
        
        return damages
    
    def _detect_train_presence(self, image):
        """
        Detect if there's actually a train/wagon in the frame.
        
        Uses multiple heuristics:
        1. Edge density in the train region (trains have strong horizontal edges)
        2. Color variance (trains have distinct colors vs background)
        3. Horizontal line detection (trains have strong horizontal features)
        
        Returns:
            tuple: (has_train: bool, coverage: float)
                   coverage is the estimated percentage of frame occupied by train
        """
        try:
            h, w = image.shape[:2]
            
            # Focus on lower 60% where trains typically appear
            train_region_top = int(h * 0.40)
            train_region = image[train_region_top:, :]
            
            # Convert to grayscale
            gray = cv2.cvtColor(train_region, cv2.COLOR_BGR2GRAY)
            
            # Method 1: Edge density analysis
            # Trains have strong edges due to their metal structure
            edges = cv2.Canny(gray, 50, 150)
            edge_density = np.sum(edges > 0) / edges.size
            
            # Method 2: Horizontal line detection
            # Trains have strong horizontal lines (windows, body panels, etc.)
            lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=50, 
                                   minLineLength=int(w*0.1), maxLineGap=10)
            
            horizontal_lines = 0
            if lines is not None:
                for line in lines:
                    x1, y1, x2, y2 = line[0]
                    # Check if line is roughly horizontal (angle < 30 degrees)
                    angle = abs(np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi)
                    if angle < 30 or angle > 150:
                        horizontal_lines += 1
            
            # Method 3: Color variance in train region
            # Trains (especially wagons) have distinct, consistent colors
            # Background has more varied colors
            hsv = cv2.cvtColor(train_region, cv2.COLOR_BGR2HSV)
            color_std = np.std(hsv[:, :, 0])  # Hue standard deviation
            
            # Method 4: Connected component analysis
            # A train creates large connected regions
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
            morph = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
            
            num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(morph, connectivity=8)
            
            # Find largest connected component (excluding background)
            if num_labels > 1:
                # Get areas of all components except background (index 0)
                areas = stats[1:, cv2.CC_STAT_AREA]
                largest_area = np.max(areas) if len(areas) > 0 else 0
                coverage = largest_area / (train_region.shape[0] * train_region.shape[1])
            else:
                coverage = 0.0
            
            # Decision logic with multiple criteria
            has_train = False
            reasons = []
            
            # Primary indicator: large connected component
            if coverage >= self.min_train_coverage:
                has_train = True
                reasons.append(f"coverage={coverage*100:.1f}%")
            
            # Secondary indicators (boost confidence)
            if edge_density > 0.05:  # Sufficient edge density
                reasons.append(f"edges={edge_density*100:.1f}%")
                if coverage >= self.min_train_coverage * 0.7:  # Slightly relaxed threshold
                    has_train = True
            
            if horizontal_lines > 5:  # Multiple horizontal lines detected
                reasons.append(f"h_lines={horizontal_lines}")
                if coverage >= self.min_train_coverage * 0.7:
                    has_train = True
            
            # Color variance check (trains have lower variance than cluttered backgrounds)
            if color_std < 40:  # Consistent color
                reasons.append(f"color_std={color_std:.1f}")
            
            if has_train:
                print(f"[TRAIN DETECTION] ✓ Train present: {', '.join(reasons)}")
            else:
                print(f"[TRAIN DETECTION] ✗ No train: coverage={coverage*100:.1f}%, edges={edge_density*100:.1f}%, lines={horizontal_lines}")
            
            return has_train, coverage
            
        except Exception as e:
            print(f"Error in train detection: {e}")
            # If detection fails, be conservative and return False
            return False, 0.0
    
    def _detect_window_door_regions(self, image):
        """Detect rectangular window/door regions in wagon image.
        
        Uses simple computer vision to find rectangular regions that likely
        represent windows and doors. Only searches in lower 60% of image
        where trains are typically located.
        """
        regions = []
        
        try:
            img_height = image.shape[0]
            
            # Only analyze lower 60% of image (where trains are)
            # This prevents detecting objects above train (sky, buildings, etc.)
            train_region_top = int(img_height * 0.40)  # Start at 40% from top
            train_region = image[train_region_top:, :]
            
            # Convert to grayscale
            gray = cv2.cvtColor(train_region, cv2.COLOR_BGR2GRAY)
            
            # Apply edge detection
            edges = cv2.Canny(gray, 50, 150)
            
            # Find contours
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                # Approximate contour to polygon
                epsilon = 0.02 * cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, epsilon, True)
                
                # Look for rectangular shapes (4 corners)
                if len(approx) >= 4:
                    x, y, w, h = cv2.boundingRect(contour)
                    area = w * h
                    
                    # Filter by size - windows/doors are moderate sized
                    # Typically 2-30% of train region area
                    region_area = train_region.shape[0] * train_region.shape[1]
                    if 0.02 * region_area < area < 0.35 * region_area:
                        # Check aspect ratio - windows/doors are roughly rectangular
                        aspect_ratio = w / h if h > 0 else 0
                        if 0.3 < aspect_ratio < 3.0:
                            # Adjust y-coordinate back to full image coordinates
                            regions.append({
                                'bbox': (x, y + train_region_top, w, h),
                                'type': 'window_door',
                                'area': area
                            })
            
            # Sort by area (largest first) and limit to top 8 regions
            regions = sorted(regions, key=lambda r: r['area'], reverse=True)[:8]
            
            if regions:
                print(f"[DAMAGE DETECTOR] Found {len(regions)} window/door regions in train area (lower 60%)")
            
        except Exception as e:
            print(f"Error detecting window/door regions: {e}")
        
        return regions
    
    def _filter_damages(self, damages, min_confidence=0.85):
        """Filter and deduplicate detected damages."""
        if not damages:
            return []
        
        # Filter by confidence
        damages = [d for d in damages if d['confidence'] >= min_confidence]
        
        # Sort by confidence (highest first)
        damages.sort(key=lambda x: x['confidence'], reverse=True)
        
        # Remove overlapping detections (non-maximum suppression)
        filtered = []
        for damage in damages:
            x1, y1, w1, h1 = damage['bbox']
            
            # Check if it overlaps significantly with any kept damage
            overlaps = False
            for kept in filtered:
                x2, y2, w2, h2 = kept['bbox']
                
                # Calculate IoU (Intersection over Union)
                xi1, yi1 = max(x1, x2), max(y1, y2)
                xi2, yi2 = min(x1 + w1, x2 + w2), min(y1 + h1, y2 + h2)
                
                inter_area = max(0, xi2 - xi1) * max(0, yi2 - yi1)
                union_area = w1 * h1 + w2 * h2 - inter_area
                
                iou = inter_area / (union_area + 1e-6)
                
                if iou > 0.5:  # Significant overlap
                    overlaps = True
                    break
            
            if not overlaps:
                filtered.append(damage)
        
        return filtered
    
    def _empty_result(self):
        """Return empty result when no valid image."""
        return {
            'has_damage': False,
            'damage_type': None,
            'damage_types': [],
            'confidence': 0.0,
            'damage_count': 0,
            'damages': [],
            'annotated_image': None,
            'train_coverage': 0.0
        }


def test_damage_detector():
    """Test the damage detector with sample images."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python damage_detector.py <image_path>")
        return
    
    image_path = sys.argv[1]
    image = cv2.imread(image_path)
    
    if image is None:
        print(f"Error: Could not load image from {image_path}")
        return
    
    detector = WagonDamageDetector()
    result = detector.detect_damage(image)
    
    print(f"\nDamage Detection Results:")
    print(f"  Has Damage: {result['has_damage']}")
    print(f"  Damage Count: {result['damage_count']}")
    print(f"  Damage Type: {result['damage_type']}")
    print(f"  Confidence: {result['confidence']:.2%}")
    
    if result['has_damage']:
        print(f"\n  Detected Damages:")
        for i, damage in enumerate(result['damages'], 1):
            print(f"    {i}. Type: {damage['type']}, "
                  f"Confidence: {damage['confidence']:.2%}, "
                  f"BBox: {damage['bbox']}")
    
    # Save annotated image
    if result['annotated_image'] is not None:
        output_path = Path(image_path).stem + '_damage_detected.jpg'
        cv2.imwrite(output_path, result['annotated_image'])
        print(f"\n  Annotated image saved to: {output_path}")


if __name__ == '__main__':
    test_damage_detector()
