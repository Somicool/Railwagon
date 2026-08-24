"""
ROI Detector Module - YOLO-based Object Detection
==================================================

Detects regions of interest in railway wagon frames:
- wagon_number: Text regions for OCR
- window: Window areas for damage inspection
- door: Door areas for damage inspection

Author: Railway Wagon Inspection System
Date: January 4, 2026
"""

import cv2
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple, Optional

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    print("[WARNING] ultralytics not installed. Install with: pip install ultralytics")


class ROIDetector:
    """Detects wagon components using YOLOv8."""
    
    # Class mapping for YOLO model
    CLASS_NAMES = {
        0: 'wagon_number',
        1: 'window',
        2: 'door'
    }
    
    def __init__(self, model_path: str = 'models/wagon_detector.pt', 
                 confidence_threshold: float = 0.4,
                 device: str = 'cpu'):
        """
        Initialize ROI detector.
        
        Args:
            model_path: Path to trained YOLOv8 model
            confidence_threshold: Minimum confidence for detections (0.0-1.0)
            device: 'cpu' or 'cuda'
        """
        self.model_path = model_path
        self.confidence_threshold = confidence_threshold
        self.device = device
        self.model = None
        
        print(f"[ROI Detector] Initialized")
        print(f"  Model: {model_path}")
        print(f"  Confidence threshold: {confidence_threshold}")
        print(f"  Device: {device}")
    
    def load_model(self):
        """Load YOLO model (lazy loading)."""
        if self.model is not None:
            return True
        
        if not YOLO_AVAILABLE:
            print("[ERROR] YOLO not available. Cannot load detector.")
            return False
        
        try:
            print(f"[ROI Detector] Loading YOLO model from {self.model_path}...")
            
            # Check if model exists
            if not Path(self.model_path).exists():
                print(f"[WARNING] Model file not found: {self.model_path}")
                print(f"[INFO] Using YOLOv8 pre-trained model as placeholder")
                # Use pre-trained COCO model as fallback for demo
                self.model = YOLO('yolov8n.pt')
                self._use_mock_detection = True
            else:
                self.model = YOLO(self.model_path)
                self._use_mock_detection = False
            
            # Move to device
            if self.device == 'cuda':
                self.model.to('cuda')
            
            print(f"[ROI Detector] Model loaded successfully")
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to load YOLO model: {e}")
            self._use_mock_detection = True
            return False
    
    def detect_rois(self, image: np.ndarray) -> List[Dict]:
        """
        Detect all ROIs in an image.
        
        Args:
            image: Input image (BGR format)
            
        Returns:
            List of detections, each containing:
            {
                'class': str,           # 'wagon_number', 'window', or 'door'
                'bbox': (x, y, w, h),   # Bounding box coordinates
                'confidence': float,     # Detection confidence
                'crop': np.ndarray      # Cropped ROI image
            }
        """
        if image is None or image.size == 0:
            return []
        
        # Load model if not loaded
        if self.model is None:
            if not self.load_model():
                # Use mock detection for demo
                return self._mock_detection(image)
        
        if self._use_mock_detection:
            return self._mock_detection(image)
        
        try:
            # Run YOLO inference
            results = self.model(image, conf=self.confidence_threshold, verbose=False)
            
            detections = []
            
            # Process each detection
            for result in results:
                boxes = result.boxes
                
                for box in boxes:
                    # Extract box data
                    x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                    confidence = float(box.conf[0])
                    class_id = int(box.cls[0])
                    
                    # Convert to xywh format
                    x, y = x1, y1
                    w, h = x2 - x1, y2 - y1
                    
                    # Get class name
                    class_name = self.CLASS_NAMES.get(class_id, 'unknown')
                    
                    # Crop ROI from image
                    crop = image[y1:y2, x1:x2].copy()
                    
                    detections.append({
                        'class': class_name,
                        'bbox': (x, y, w, h),
                        'confidence': confidence,
                        'crop': crop
                    })
            
            return detections
            
        except Exception as e:
            print(f"[ERROR] YOLO detection failed: {e}")
            return []
    
    def _mock_detection(self, image: np.ndarray) -> List[Dict]:
        """
        Mock detection for demo/testing when YOLO model not available.
        Creates plausible ROI regions based on typical wagon layout.
        
        Args:
            image: Input image
            
        Returns:
            List of mock detections
        """
        h, w = image.shape[:2]
        
        detections = []
        
        # Mock wagon number region (typically upper middle of wagon)
        wagon_number_box = (
            int(w * 0.35),  # x
            int(h * 0.15),  # y
            int(w * 0.30),  # width
            int(h * 0.15)   # height
        )
        x, y, box_w, box_h = wagon_number_box
        crop = image[y:y+box_h, x:x+box_w].copy()
        
        detections.append({
            'class': 'wagon_number',
            'bbox': wagon_number_box,
            'confidence': 0.85,
            'crop': crop
        })
        
        # Mock window regions (2 windows on left and right)
        for i, x_pos in enumerate([0.15, 0.65]):
            window_box = (
                int(w * x_pos),
                int(h * 0.35),
                int(w * 0.20),
                int(h * 0.30)
            )
            x, y, box_w, box_h = window_box
            crop = image[y:y+box_h, x:x+box_w].copy()
            
            detections.append({
                'class': 'window',
                'bbox': window_box,
                'confidence': 0.75 + i * 0.05,
                'crop': crop
            })
        
        # Mock door region (typically right side)
        door_box = (
            int(w * 0.75),
            int(h * 0.25),
            int(w * 0.15),
            int(h * 0.50)
        )
        x, y, box_w, box_h = door_box
        crop = image[y:y+box_h, x:x+box_w].copy()
        
        detections.append({
            'class': 'door',
            'bbox': door_box,
            'confidence': 0.72,
            'crop': crop
        })
        
        print(f"[MOCK] Generated {len(detections)} mock detections")
        return detections
    
    def filter_by_class(self, detections: List[Dict], class_name: str) -> List[Dict]:
        """Filter detections by class name."""
        return [d for d in detections if d['class'] == class_name]
    
    def filter_by_confidence(self, detections: List[Dict], min_conf: float) -> List[Dict]:
        """Filter detections by minimum confidence."""
        return [d for d in detections if d['confidence'] >= min_conf]
    
    def draw_detections(self, image: np.ndarray, detections: List[Dict]) -> np.ndarray:
        """
        Draw bounding boxes on image for visualization.
        
        Args:
            image: Input image
            detections: List of detections
            
        Returns:
            Annotated image
        """
        annotated = image.copy()
        
        # Color mapping for different classes
        colors = {
            'wagon_number': (0, 255, 0),    # Green
            'window': (255, 165, 0),        # Orange
            'door': (0, 165, 255)           # Blue
        }
        
        for det in detections:
            x, y, w, h = det['bbox']
            class_name = det['class']
            confidence = det['confidence']
            
            color = colors.get(class_name, (255, 255, 255))
            
            # Draw bounding box
            cv2.rectangle(annotated, (x, y), (x + w, y + h), color, 2)
            
            # Draw label
            label = f"{class_name}: {confidence:.2f}"
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
            
            # Label background
            cv2.rectangle(annotated, (x, y - label_size[1] - 10), 
                         (x + label_size[0], y), color, -1)
            
            # Label text
            cv2.putText(annotated, label, (x, y - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        
        return annotated


def test_roi_detector():
    """Test the ROI detector with a sample image."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python roi_detector.py <image_path>")
        return
    
    image_path = sys.argv[1]
    image = cv2.imread(image_path)
    
    if image is None:
        print(f"Error: Could not load image from {image_path}")
        return
    
    # Initialize detector
    detector = ROIDetector(confidence_threshold=0.3)
    
    # Detect ROIs
    detections = detector.detect_rois(image)
    
    print(f"\nDetected {len(detections)} ROIs:")
    for i, det in enumerate(detections, 1):
        print(f"{i}. {det['class']}: confidence={det['confidence']:.2f}, bbox={det['bbox']}")
    
    # Draw detections
    annotated = detector.draw_detections(image, detections)
    
    # Save annotated image
    output_path = Path(image_path).stem + '_roi_detections.jpg'
    cv2.imwrite(output_path, annotated)
    print(f"\nAnnotated image saved to: {output_path}")
    
    # Save individual ROI crops
    output_dir = Path('roi_crops')
    output_dir.mkdir(exist_ok=True)
    
    for i, det in enumerate(detections):
        crop_path = output_dir / f"{det['class']}_{i}.jpg"
        cv2.imwrite(str(crop_path), det['crop'])
    
    print(f"ROI crops saved to: {output_dir}/")


if __name__ == '__main__':
    test_roi_detector()
