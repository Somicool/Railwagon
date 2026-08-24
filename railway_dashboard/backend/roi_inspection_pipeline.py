"""
ROI-Based Inspection Pipeline
==============================

Modular pipeline orchestrator for wagon inspection using ROI detection.

Pipeline Flow:
1. (Optional) Light global enhancement
2. YOLO ROI detection → wagon_number, window, door
3. Task-specific ROI enhancement
4. OCR on wagon_number ROIs
5. Damage detection on window/door ROIs
6. Save outputs with metadata

Author: Railway Wagon Inspection System
Date: January 4, 2026
"""

import cv2
import numpy as np
from pathlib import Path
from datetime import datetime
import json
from typing import Dict, List, Tuple, Optional

# Import ROI modules
from roi_detector import ROIDetector
from roi_enhancer import ROIEnhancer, GlobalEnhancer
from roi_damage_detector import ROIDamageDetector

# Import OCR (assuming easyocr is available)
try:
    import easyocr
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    print("[WARNING] easyocr not installed. OCR will be simulated.")


class ROIInspectionPipeline:
    """Main pipeline orchestrator for ROI-based wagon inspection."""
    
    def __init__(self, 
                 yolo_model_path: str = 'models/wagon_detector.pt',
                 output_base_dir: str = 'records',
                 use_global_enhancement: bool = False,
                 device: str = 'cpu'):
        """
        Initialize ROI-based inspection pipeline.
        
        Args:
            yolo_model_path: Path to trained YOLO model
            output_base_dir: Base directory for saving outputs
            use_global_enhancement: Enable optional global frame enhancement
            device: 'cpu' or 'cuda'
        """
        self.output_base_dir = Path(output_base_dir)
        self.output_base_dir.mkdir(exist_ok=True)
        self.use_global_enhancement = use_global_enhancement
        self.device = device
        
        # Initialize modules
        print("\n" + "="*60)
        print("ROI-BASED INSPECTION PIPELINE INITIALIZATION")
        print("="*60)
        
        self.roi_detector = ROIDetector(
            model_path=yolo_model_path,
            confidence_threshold=0.4,
            device=device
        )
        
        self.roi_enhancer = ROIEnhancer()
        self.global_enhancer = GlobalEnhancer()
        self.damage_detector = ROIDamageDetector(sensitivity='medium')
        
        # OCR reader (lazy loading)
        self.ocr_reader = None
        
        print(f"\nGlobal Enhancement: {'ENABLED' if use_global_enhancement else 'DISABLED'}")
        print("="*60 + "\n")
    
    def _load_ocr(self):
        """Load OCR reader (lazy loading)."""
        if self.ocr_reader is not None:
            return True
        
        if not OCR_AVAILABLE:
            print("[WARNING] OCR not available, will use mock OCR")
            return False
        
        try:
            print("[OCR] Loading EasyOCR...")
            self.ocr_reader = easyocr.Reader(['en'], gpu=(self.device == 'cuda'))
            print("[OCR] EasyOCR loaded successfully")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to load OCR: {e}")
            return False
    
    def process_frame(self, frame: np.ndarray, frame_id: str = None) -> Dict:
        """
        Process single frame through ROI pipeline.
        
        Args:
            frame: Input video frame (BGR)
            frame_id: Optional frame identifier (for logging)
            
        Returns:
            Processing results dictionary
        """
        if frame_id is None:
            frame_id = f"frame_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        print(f"\n[PIPELINE] Processing {frame_id}")
        
        results = {
            'frame_id': frame_id,
            'wagon_numbers': [],
            'damage_detections': [],
            'roi_detections': [],
            'processing_stages': {}
        }
        
        # STAGE 1: Optional global enhancement
        if self.use_global_enhancement:
            frame = self.global_enhancer.enhance_frame(frame, apply=True)
            results['processing_stages']['global_enhancement'] = 'applied'
        else:
            results['processing_stages']['global_enhancement'] = 'skipped'
        
        # STAGE 2: YOLO ROI detection
        print(f"[STAGE 2] Running YOLO detection...")
        detections = self.roi_detector.detect_rois(frame)
        results['roi_detections'] = len(detections)
        results['processing_stages']['roi_detection'] = f"{len(detections)} ROIs found"
        
        # Store frame for context validation
        self._current_frame = frame
        
        if len(detections) == 0:
            print("[PIPELINE] No ROIs detected")
            return results
        
        print(f"[STAGE 2] Detected {len(detections)} ROIs")
        for det in detections:
            print(f"  - {det['class']}: confidence={det['confidence']:.2f}, bbox={det['bbox']}")
        
        # STAGE 3: Process each ROI
        for i, detection in enumerate(detections):
            roi_class = detection['class']
            roi_crop = detection['crop']
            confidence = detection['confidence']
            bbox = detection['bbox']
            
            print(f"\n[STAGE 3] Processing ROI #{i+1}: {roi_class}")
            
            # STAGE 3A: Task-specific enhancement
            enhanced_roi = self.roi_enhancer.enhance_roi(roi_crop, roi_class)
            
            # STAGE 3B: Task-specific processing
            if roi_class == 'wagon_number':
                # OCR PROCESSING
                ocr_result = self._process_wagon_number(enhanced_roi, detection, i)
                if ocr_result:
                    results['wagon_numbers'].append(ocr_result)
            
            elif roi_class in ['window', 'door']:
                # DAMAGE DETECTION
                damage_result = self._process_damage_roi(enhanced_roi, detection, i, self._current_frame)
                if damage_result and damage_result['has_damage']:
                    results['damage_detections'].append(damage_result)
        
        print(f"\n[PIPELINE] Frame {frame_id} processing complete")
        print(f"  Wagon Numbers: {len(results['wagon_numbers'])}")
        print(f"  Damage Detections: {len(results['damage_detections'])}")
        
        return results
    
    def _process_wagon_number(self, enhanced_roi: np.ndarray, detection: Dict, roi_idx: int) -> Optional[Dict]:
        """
        Process wagon number ROI with OCR.
        
        Args:
            enhanced_roi: Enhanced ROI image
            detection: Original detection info
            roi_idx: ROI index
            
        Returns:
            OCR result dictionary or None
        """
        print(f"[OCR] Processing wagon number ROI #{roi_idx}")
        
        # Load OCR if not loaded
        if self.ocr_reader is None:
            self._load_ocr()
        
        # Run OCR
        if self.ocr_reader:
            try:
                # EasyOCR expects RGB
                rgb_roi = cv2.cvtColor(enhanced_roi, cv2.COLOR_BGR2RGB)
                ocr_results = self.ocr_reader.readtext(rgb_roi)
                
                if ocr_results:
                    # Get highest confidence result
                    best_result = max(ocr_results, key=lambda x: x[2])
                    text = best_result[1]
                    conf = best_result[2]
                    
                    print(f"[OCR] Detected: '{text}' (confidence: {conf:.2f})")
                    
                    return {
                        'text': text,
                        'confidence': conf,
                        'bbox': detection['bbox'],
                        'detection_confidence': detection['confidence'],
                        'roi_index': roi_idx
                    }
                else:
                    print(f"[OCR] No text detected")
                    return None
                    
            except Exception as e:
                print(f"[OCR ERROR] {e}")
                return None
        else:
            # Mock OCR for demo
            print(f"[MOCK OCR] Simulating OCR...")
            return {
                'text': f'MOCK-{roi_idx:03d}',
                'confidence': 0.75,
                'bbox': detection['bbox'],
                'detection_confidence': detection['confidence'],
                'roi_index': roi_idx
            }
    
    def _process_damage_roi(self, enhanced_roi: np.ndarray, detection: Dict, roi_idx: int, full_frame: np.ndarray = None) -> Optional[Dict]:
        """
        Process window/door ROI for damage detection.
        
        Args:
            enhanced_roi: Enhanced ROI image
            detection: Original detection info
            roi_idx: ROI index
            full_frame: Full frame for train context validation
            
        Returns:
            Damage detection result or None
        """
        roi_class = detection['class']
        bbox = detection['bbox']
        print(f"[DAMAGE] Analyzing {roi_class} ROI #{roi_idx} at {bbox}")
        
        # Run damage detection with train context validation
        damage_result = self.damage_detector.analyze_damage(
            enhanced_roi, 
            roi_class,
            full_frame=full_frame,
            bbox=bbox
        )
        
        # Check validation status
        if 'validation' in damage_result and not damage_result['validation'].get('is_train_roi', True):
            print(f"[DAMAGE] Skipped - ROI rejected as background")
            return None
        
        if damage_result['has_damage']:
            print(f"[DAMAGE] FOUND: {damage_result['damage_type']} "
                  f"(confidence: {damage_result['confidence']:.2f})")
        else:
            print(f"[DAMAGE] No damage detected")
        
        # Add metadata
        damage_result['roi_class'] = roi_class
        damage_result['bbox'] = detection['bbox']
        damage_result['detection_confidence'] = detection['confidence']
        damage_result['roi_index'] = roi_idx
        
        return damage_result
    
    def process_video(self, video_path: str, inspection_id: str = None) -> Dict:
        """
        Process entire video file.
        
        Args:
            video_path: Path to input video
            inspection_id: Unique inspection identifier
            
        Returns:
            Complete inspection results
        """
        if inspection_id is None:
            inspection_id = datetime.now().strftime('inspection_%Y%m%d_%H%M%S')
        
        print(f"\n{'='*60}")
        print(f"VIDEO INSPECTION: {inspection_id}")
        print(f"Video: {video_path}")
        print(f"{'='*60}\n")
        
        # Create output directories
        output_dir = self.output_base_dir / inspection_id
        output_dir.mkdir(exist_ok=True)
        
        wagon_numbers_dir = output_dir / 'wagon_numbers'
        damage_dir = output_dir / 'damage'
        wagon_numbers_dir.mkdir(exist_ok=True)
        damage_dir.mkdir(exist_ok=True)
        
        # Open video
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"[ERROR] Could not open video: {video_path}")
            return {'error': 'Failed to open video'}
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        print(f"Video Info: {total_frames} frames @ {fps:.1f} FPS\n")
        
        # Inspection results
        inspection_results = {
            'inspection_id': inspection_id,
            'video_path': video_path,
            'total_frames': total_frames,
            'frames_processed': 0,
            'wagon_numbers_found': [],
            'damage_detections_found': [],
            'start_time': datetime.now().isoformat()
        }
        
        frame_count = 0
        processed_count = 0
        
        # Process frames (sample every Nth frame for efficiency)
        frame_skip = 5  # Process every 5th frame
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_count += 1
            
            # Skip frames for efficiency
            if frame_count % frame_skip != 0:
                continue
            
            processed_count += 1
            frame_id = f"frame_{frame_count:06d}"
            
            # Process frame
            results = self.process_frame(frame, frame_id)
            
            # Save wagon number crops
            for wn in results['wagon_numbers']:
                wn_path = wagon_numbers_dir / f"wagon_{wn['text']}_{frame_count}.jpg"
                x, y, w, h = wn['bbox']
                crop = frame[y:y+h, x:x+w]
                cv2.imwrite(str(wn_path), crop)
                
                inspection_results['wagon_numbers_found'].append({
                    'text': wn['text'],
                    'confidence': wn['confidence'],
                    'frame': frame_count,
                    'path': str(wn_path.relative_to(self.output_base_dir))
                })
            
            # Save damage crops
            for dmg in results['damage_detections']:
                dmg_path = damage_dir / f"damage_{dmg['damage_type']}_{frame_count}.jpg"
                x, y, w, h = dmg['bbox']
                crop = frame[y:y+h, x:x+w]
                
                # Annotate damage crop
                annotated_crop = self.damage_detector.annotate_damage(crop, dmg)
                cv2.imwrite(str(dmg_path), annotated_crop)
                
                inspection_results['damage_detections_found'].append({
                    'damage_type': dmg['damage_type'],
                    'confidence': dmg['confidence'],
                    'roi_class': dmg['roi_class'],
                    'frame': frame_count,
                    'path': str(dmg_path.relative_to(self.output_base_dir))
                })
            
            # Progress update
            if processed_count % 10 == 0:
                progress = (frame_count / total_frames) * 100
                print(f"[PROGRESS] {progress:.1f}% ({frame_count}/{total_frames} frames)")
        
        cap.release()
        
        inspection_results['frames_processed'] = processed_count
        inspection_results['end_time'] = datetime.now().isoformat()
        
        # Save metadata
        metadata_path = output_dir / 'inspection_metadata.json'
        with open(metadata_path, 'w') as f:
            json.dump(inspection_results, f, indent=2)
        
        print(f"\n{'='*60}")
        print(f"INSPECTION COMPLETE")
        print(f"{'='*60}")
        print(f"Frames Processed: {processed_count}/{total_frames}")
        print(f"Wagon Numbers: {len(inspection_results['wagon_numbers_found'])}")
        print(f"Damage Detections: {len(inspection_results['damage_detections_found'])}")
        print(f"Output: {output_dir}")
        print(f"{'='*60}\n")
        
        return inspection_results


def demo_pipeline():
    """Demo the ROI inspection pipeline."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python roi_inspection_pipeline.py <video_path>")
        print("\nExample:")
        print("  python roi_inspection_pipeline.py test_video.mp4")
        return
    
    video_path = sys.argv[1]
    
    # Initialize pipeline
    pipeline = ROIInspectionPipeline(
        yolo_model_path='models/wagon_detector.pt',
        output_base_dir='records',
        use_global_enhancement=False,  # OPTIONAL - set to True if needed
        device='cpu'
    )
    
    # Process video
    results = pipeline.process_video(video_path)
    
    print("\nInspection Summary:")
    print(f"  Inspection ID: {results['inspection_id']}")
    print(f"  Wagon Numbers Found: {len(results['wagon_numbers_found'])}")
    print(f"  Damage Detections: {len(results['damage_detections_found'])}")
    
    if results['wagon_numbers_found']:
        print("\n  Detected Wagon Numbers:")
        for wn in results['wagon_numbers_found'][:5]:  # Show first 5
            print(f"    - {wn['text']} (Frame {wn['frame']}, Conf: {wn['confidence']:.2f})")
    
    if results['damage_detections_found']:
        print("\n  Damage Detections:")
        for dmg in results['damage_detections_found'][:5]:  # Show first 5
            print(f"    - {dmg['damage_type']} on {dmg['roi_class']} "
                  f"(Frame {dmg['frame']}, Conf: {dmg['confidence']:.2f})")


if __name__ == '__main__':
    demo_pipeline()
