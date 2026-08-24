"""
Inspection Processor Module
============================

Integrates existing deblurring and OCR pipelines for railway wagon inspection.
Handles live video, recorded video, and single image processing.

Author: Railway Wagon Inspection System
Date: December 25, 2025
"""

import cv2
import torch
import numpy as np
from pathlib import Path
import json
import time
from datetime import datetime
import threading
import base64
from damage_detector import WagonDamageDetector


class InspectionProcessor:
    """Process video streams and images for wagon inspection."""
    
    def __init__(self):
        """Initialize processor with models and OCR."""
        self.live_video_active = False
        self.camera = None
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Session tracking
        self.sessions = {}
        self.stop_flags = {}
        
        # Initialize models (lazy loading)
        self.deblur_model = None
        self.ocr_reader = None
        self.damage_detector = None  # Damage detection for windows/doors
        
        # Motion detection using OpenCV Background Subtraction
        self.prev_frame = None
        self.motion_threshold = 3.5  # Balanced sensitivity (not too sensitive)
        self.min_contour_area = 3000  # Minimum area to filter small movements
        
        # TWO-STAGE MOTION DETECTION: Motion Candidate → Train Confirmation
        # Stage 1: Motion Candidate Detection
        self.motion_frames_to_candidate = 3  # 3 frames for candidate (balanced)
        
        # Stage 2: Train Confirmation Rules (STRICT to avoid false positives)
        self.train_confirmation_frames = 4  # 4 frames to confirm (reject transient motion)
        self.train_min_width_ratio = 0.25  # Train must be reasonably wide (25% of frame)
        self.train_min_height_ratio = 0.12  # Train must have some height (12% of frame)
        self.train_aspect_ratio_min = 2.0  # Trains are wide horizontal objects
        self.train_horizontal_motion = True  # Must have horizontal movement
        
        # Stage 3: Inspection Stop Rules
        self.no_motion_frames_to_stop = 3  # Just 3 frames below threshold to stop
        self.stop_motion_threshold = 20.0  # If motion drops below 20%, stop capturing
        
        # State Machine
        self.motion_state = 'IDLE'  # IDLE, MOTION_CANDIDATE, TRAIN_CONFIRMED, INSPECTION_RUNNING
        self.candidate_frame_count = 0
        self.train_confirmation_count = 0
        self.no_motion_count = 0
        
        # Learning period
        self.learning_frames = 20  # Better background learning (balance speed vs accuracy)
        self.frame_count_since_reset = 0
        
        # Frame dimensions (set when first frame received)
        self.frame_width = None
        self.frame_height = None
        
        # Train candidate tracking
        self.current_train_bbox = None  # (x, y, w, h) of detected train region
        
        # Initialize OpenCV Background Subtractors (for robust motion detection)
        # MOG2 (Mixture of Gaussians) - Good for outdoor scenes with shadows
        self.bg_subtractor_mog2 = cv2.createBackgroundSubtractorMOG2(
            history=250,           # Background model history
            varThreshold=20,       # Balanced sensitivity (not too sensitive)
            detectShadows=True     # Detect and mark shadows (improves accuracy)
        )
        
        # KNN (K-Nearest Neighbors) - Better for indoor/controlled lighting
        self.bg_subtractor_knn = cv2.createBackgroundSubtractorKNN(
            history=500,           # Number of frames for background model (INCREASED)
            dist2Threshold=1200.0, # Threshold for squared distance (50% INCREASE - much less sensitive)
            detectShadows=True     # Detect and mark shadows
        )
        
        # Motion detection method: 'frame_diff', 'mog2', 'knn', 'combined'
        self.motion_detection_method = 'mog2'  # Default to MOG2
        
        print(f"Inspection Processor initialized (Device: {self.device})")
        print(f"Motion Detection Method: {self.motion_detection_method.upper()}")
    
    def _load_deblur_model(self):
        """Load deblurring model (lazy loading)."""
        if self.deblur_model is not None:
            return
        
        try:
            import sys
            sys.path.append(str(Path(__file__).parent.parent.parent / 'models'))
            from mimo_unet_plus import MIMOUNetPlus
            
            print("=" * 60)
            print("Loading Fine-Tuned MIMOUNetPlus Model...")
            print("=" * 60)
            
            # Use fine-tuned MIMOUNetPlus (custom architecture)
            self.deblur_model = MIMOUNetPlus()
            print("✓ Model architecture: MIMOUNetPlus (Fine-tuned)")
            
            # Try to load weights - prioritize improved fine-tuned model
            # Checkpoints are in the parent directory (blur/checkpoints)
            checkpoints_base = Path(__file__).parent.parent.parent / 'checkpoints'
            weight_paths = [
                checkpoints_base / 'best_model_improved.pkl',  # Improved model (29.86 dB)
                checkpoints_base / 'best_model.pkl',           # Original fine-tuned (25.30 dB)
            ]
            
            weights_loaded = False
            for weight_path in weight_paths:
                if weight_path.exists():
                    try:
                        print(f"Trying: {weight_path.name}")
                        checkpoint = torch.load(str(weight_path), map_location=self.device, weights_only=False)
                        
                        # Handle different checkpoint formats
                        if isinstance(checkpoint, dict):
                            if 'model' in checkpoint:
                                state_dict = checkpoint['model']
                            elif 'model_state_dict' in checkpoint:
                                state_dict = checkpoint['model_state_dict']
                            elif 'state_dict' in checkpoint:
                                state_dict = checkpoint['state_dict']
                            else:
                                state_dict = checkpoint
                        else:
                            state_dict = checkpoint
                        
                        missing, unexpected = self.deblur_model.load_state_dict(state_dict, strict=False)
                        loaded_keys = len(state_dict) - len(missing)
                        total_keys = len(state_dict)
                        
                        print(f"✓ Loaded {loaded_keys}/{total_keys} parameters")
                        if len(missing) > 0:
                            print(f"  ⚠ Missing: {len(missing)} parameters")
                        if len(unexpected) > 0:
                            print(f"  ⚠ Unexpected: {len(unexpected)} parameters")
                        
                        print(f"✓✓✓ Successfully loaded weights from: {weight_path.name} ✓✓✓")
                        weights_loaded = True
                        break
                    except Exception as e:
                        print(f"  ✗ Failed: {e}")
                        continue
            
            if not weights_loaded:
                print("⚠⚠⚠ WARNING: No pretrained weights found! ⚠⚠⚠")
                print("Deblurring will NOT work properly without weights!")
                print("Please ensure weights files exist in the weights/ directory")
                print("=" * 60)
                self.deblur_model = None
                return
            
            self.deblur_model.to(self.device)
            self.deblur_model.eval()
            print("=" * 60)
            print("✓✓✓ Deblurring Model Ready ✓✓✓")
            print("=" * 60)
            
        except Exception as e:
            print(f"=" * 60)
            print(f"ERROR: Could not load deblur model: {e}")
            print("=" * 60)
            import traceback
            traceback.print_exc()
            self.deblur_model = None
    
    def _load_ocr_reader(self):
        """Load OCR reader (lazy loading)."""
        if self.ocr_reader is not None:
            return
        
        try:
            import easyocr
            print("Loading EasyOCR...")
            self.ocr_reader = easyocr.Reader(['en'], gpu=torch.cuda.is_available())
            print("EasyOCR loaded successfully")
        except Exception as e:
            print(f"Warning: Could not load EasyOCR: {e}")
            print("Will proceed without OCR")
    
    def _load_damage_detector(self):
        """Load damage detector (lazy loading)."""
        if self.damage_detector is not None:
            return
        
        try:
            print("Loading Wagon Damage Detector...")
            self.damage_detector = WagonDamageDetector(device=str(self.device))
            print("Damage Detector loaded successfully")
        except Exception as e:
            print(f"Warning: Could not load Damage Detector: {e}")
            print("Will proceed without damage detection")
    
    # ====================================================
    # LIVE VIDEO FUNCTIONS
    # ====================================================
    
    def start_live_video(self, video_source=0):
        """Start live video feed from camera or URL."""
        print(f"\n[VIDEO] ===========================================")
        print(f"[VIDEO] start_live_video() called")
        print(f"[VIDEO] Source: {video_source}")
        print(f"[VIDEO] ===========================================\n")
        
        try:
            # Try multiple sources if URL fails
            sources_to_try = []
            
            if isinstance(video_source, str):
                # If URL provided, try it first, then fallback to camera indices
                sources_to_try = [video_source, 1, 2]  # Try URL, then cameras 1, 2 (skip 0 - that's webcam)
                print(f"[VIDEO] URL provided. Will try fallback cameras if URL fails")
            else:
                # Camera index provided - use it exclusively without fallback
                sources_to_try = [video_source]
            
            for source in sources_to_try:
                print(f"[VIDEO] Trying source: {source}")
                
                # Open camera
                if isinstance(source, str):
                    # For URL, use CAP_FFMPEG backend
                    self.camera = cv2.VideoCapture(source, cv2.CAP_FFMPEG)
                else:
                    # For camera index, try default backend first, then DSHOW if fails
                    self.camera = cv2.VideoCapture(source)
                    if not self.camera.isOpened():
                        print(f"[VIDEO] Default backend failed, trying DSHOW...")
                        self.camera = cv2.VideoCapture(source, cv2.CAP_DSHOW)
                
                if self.camera.isOpened():
                    # Configure camera properties for better streaming
                    self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimize buffer latency
                    self.camera.set(cv2.CAP_PROP_FPS, 30)  # Request 30 FPS
                    
                    # Test if we can actually read a frame
                    ret, frame = self.camera.read()
                    if ret and frame is not None:
                        self.live_video_active = True
                        source_type = 'URL' if isinstance(source, str) else f'Camera {source}'
                        print(f"[VIDEO SUCCESS] Live video started ({source_type})")
                        print(f"[VIDEO SUCCESS] Frame shape: {frame.shape}")
                        print(f"[VIDEO SUCCESS] Resolution: {frame.shape[1]}x{frame.shape[0]}")
                        print(f"[VIDEO SUCCESS] Camera is ready for streaming")
                        return True
                    else:
                        print(f"[VIDEO] Source opened but couldn't read frame")
                        self.camera.release()
                        self.camera = None
                else:
                    print(f"[VIDEO] Failed to open: {source}")
            
            print(f"[VIDEO ERROR] All sources failed")
            print(f"[VIDEO ERROR] Make sure DroidCam Client is running OR DroidCam app is accessible")
            return False
            
        except Exception as e:
            print(f"[VIDEO ERROR] Exception starting live video: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def stop_live_video(self):
        """Stop live video feed."""
        self.live_video_active = False
        if self.camera is not None:
            self.camera.release()
            self.camera = None
        print("Live video stopped")
    
    def get_live_frame(self):
        """Get current frame from live video."""
        if self.camera is None or not self.live_video_active:
            return None
        
        # Grab and retrieve frame for better performance
        if self.camera.grab():
            ret, frame = self.camera.retrieve()
            if ret and frame is not None:
                return frame
        
        return None
    
    # ====================================================
    # INSPECTION FUNCTIONS
    # ====================================================
    
    def _detect_train_in_frame(self, frame, bbox):
        """
        Detect if there's actually a train visible in the bounding box region.
        Uses visual features like:
        - Strong horizontal edges (train profile)
        - Rectangular shapes (wagons)
        - Texture patterns consistent with trains
        
        Returns: (is_train, confidence, reason)
        """
        if bbox is None:
            return False, 0.0, "No bounding box"
        
        x, y, w, h = bbox
        
        # Extract region of interest
        roi = frame[y:y+h, x:x+w]
        if roi.size == 0:
            return False, 0.0, "Empty ROI"
        
        # Convert to grayscale
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY) if len(roi.shape) == 3 else roi
        
        # Feature 1: Detect strong horizontal edges (train profile)
        edges = cv2.Canny(gray, 50, 150)
        horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 1))
        horizontal_edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, horizontal_kernel)
        horizontal_ratio = np.sum(horizontal_edges > 0) / horizontal_edges.size
        
        # Feature 2: Detect rectangular contours (wagons)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        rect_count = 0
        for cnt in contours:
            if cv2.contourArea(cnt) < 500:
                continue
            peri = cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, 0.04 * peri, True)
            # Rectangular shapes have 4 sides
            if len(approx) == 4:
                rect_count += 1
        
        # Feature 3: Check for bottom-heavy structure (wheels/undercarriage)
        bottom_half = gray[h//2:, :]
        top_half = gray[:h//2, :]
        bottom_edge_density = np.sum(cv2.Canny(bottom_half, 50, 150) > 0) / bottom_half.size if bottom_half.size > 0 else 0
        top_edge_density = np.sum(cv2.Canny(top_half, 50, 150) > 0) / top_half.size if top_half.size > 0 else 0
        
        # Scoring system
        score = 0
        reasons = []
        
        # Strong horizontal edges (trains have clear horizontal profiles)
        if horizontal_ratio > 0.03:  # LOWERED from 0.05 for early detection
            score += 30
            reasons.append(f"horizontal_edges={horizontal_ratio:.1%}")
        
        # Multiple rectangular shapes (wagons)
        if rect_count >= 1:  # At least 1 rectangle detected
            score += 30
            reasons.append(f"rectangles={rect_count}")
        
        # Bottom-heavy (wheels/undercarriage creates more detail at bottom)
        if bottom_edge_density > top_edge_density * 0.8:  # Bottom has significant edges
            score += 20
            reasons.append(f"bottom_heavy")
        
        # Minimum texture variance (trains aren't blank)
        variance = np.var(gray)
        if variance > 100:  # Has texture
            score += 20
            reasons.append(f"texture={variance:.0f}")
        
        confidence = score / 100.0
        is_train = score >= 40  # Need 40% confidence to confirm it's a train
        
        reason = f"Score={score}/100 ({', '.join(reasons)})" if reasons else f"Score={score}/100 (no features)"
        return is_train, confidence, reason
    
    def _validate_train_candidate(self, frame, contours):
        """
        STAGE 2: TRAIN CONFIRMATION
        
        Validates if detected motion is actually a train based on:
        1. Size: Large moving region (>20% width, >10% height)
        2. Aspect Ratio: Wide object (width/height >= 2.5)
        3. Persistence: Motion sustained for N frames
        4. Direction: Horizontal movement (placeholder)
        5. NOT camera shake: Motion area must be <70% of frame
        
        Returns: (is_train, bbox, reason)
        """
        if len(contours) == 0:
            return False, None, "No contours detected"
        
        # Get frame dimensions
        if self.frame_width is None or self.frame_height is None:
            self.frame_height, self.frame_width = frame.shape[:2]
        
        # CAMERA SHAKE DETECTION: Check total motion area
        # If motion covers >70% of frame, it's camera movement, not a train
        total_motion_area = sum(cv2.contourArea(c) for c in contours)
        frame_area = self.frame_width * self.frame_height
        motion_coverage = total_motion_area / frame_area
        
        if motion_coverage > 0.70:
            return False, None, f"Camera shake detected (motion covers {motion_coverage:.1%} of frame - too much!)"
        
        # Find the largest contour (train candidate)
        largest_contour = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(largest_contour)
        
        # RULE 1: Size Check - Train must be LARGE but not TOO large
        width_ratio = w / self.frame_width
        height_ratio = h / self.frame_height
        
        # Maximum size check - trains shouldn't cover entire frame
        if width_ratio > 0.85:
            return False, (x, y, w, h), f"Too wide ({width_ratio:.1%} - probably camera shake)"
        
        if height_ratio > 0.80:
            return False, (x, y, w, h), f"Too tall ({height_ratio:.1%} - probably camera shake)"
        
        # Minimum size check
        if width_ratio < self.train_min_width_ratio:
            return False, (x, y, w, h), f"Width too small ({width_ratio:.1%} < {self.train_min_width_ratio:.0%})"
        
        if height_ratio < self.train_min_height_ratio:
            return False, (x, y, w, h), f"Height too small ({height_ratio:.1%} < {self.train_min_height_ratio:.0%})"
        
        # RULE 2: Aspect Ratio Check - Train must be WIDE
        if h == 0:
            return False, (x, y, w, h), "Invalid height"
        
        aspect_ratio = w / h
        if aspect_ratio < self.train_aspect_ratio_min:
            return False, (x, y, w, h), f"Not wide enough (aspect={aspect_ratio:.1f} < {self.train_aspect_ratio_min})"
        
        # RULE 3: Motion Direction Check - Train moves horizontally (PLACEHOLDER)
        # In real implementation, check optical flow or contour center movement
        has_horizontal_motion = self.train_horizontal_motion  # Placeholder: assume horizontal
        
        if not has_horizontal_motion:
            return False, (x, y, w, h), "No horizontal motion detected"
        
        # ALL RULES PASSED - Now check if it actually LOOKS like a train!
        is_train_visual, confidence, visual_reason = self._detect_train_in_frame(frame, (x, y, w, h))
        
        if not is_train_visual:
            return False, (x, y, w, h), f"Not a train visually: {visual_reason}"
        
        # CONFIRMED: Size, aspect ratio, AND visual features match a train!
        return True, (x, y, w, h), f"TRAIN CONFIRMED (size={width_ratio:.1%}x{height_ratio:.1%}, aspect={aspect_ratio:.1f}, coverage={motion_coverage:.1%}, {visual_reason})"
    
    def _detect_motion(self, frame):
        """
        STAGE 1: MOTION CANDIDATE DETECTION
        
        Detects if there is significant motion in the frame.
        Returns: (has_motion, motion_percentage, contours)
        """
        # Use MOG2 for motion detection
        has_motion, motion_pct, contours = self._detect_motion_mog2(frame)
        return has_motion, motion_pct, contours
    
    def _detect_motion_mog2(self, frame):
        """
        Detect motion using MOG2 Background Subtraction.
        Returns: (has_motion, motion_percentage, contours)
        """
        # During learning period, just update background model
        if self.frame_count_since_reset < self.learning_frames:
            self.bg_subtractor_mog2.apply(frame, learningRate=0.05)
            return False, 0.0, []
        
        # Apply MOG2 background subtraction
        fg_mask = self.bg_subtractor_mog2.apply(frame, learningRate=0.001)
        
        # Remove shadows
        _, fg_mask = cv2.threshold(fg_mask, 200, 255, cv2.THRESH_BINARY)
        
        # Morphological operations (lighter to preserve more motion)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel, iterations=1)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel, iterations=2)
        
        # Find contours
        contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter by minimum area
        significant_contours = [c for c in contours if cv2.contourArea(c) > self.min_contour_area]
        
        # Debug logging
        if self.frame_count_since_reset % 30 == 0:
            print(f"[MOG2 DEBUG] Total contours: {len(contours)}, Significant (>{self.min_contour_area}px): {len(significant_contours)}")
        
        if len(significant_contours) == 0:
            return False, 0.0, []
        
        # Calculate solidity check
        validated_contours = []
        for contour in significant_contours:
            hull = cv2.convexHull(contour)
            hull_area = cv2.contourArea(hull)
            if hull_area > 0:
                solidity = cv2.contourArea(contour) / hull_area
                if solidity > 0.4:
                    validated_contours.append(contour)
        
        if len(validated_contours) == 0:
            return False, 0.0, []
        
        # Calculate motion percentage
        total_area = sum(cv2.contourArea(c) for c in validated_contours)
        total_pixels = fg_mask.shape[0] * fg_mask.shape[1]
        motion_percentage = (total_area / total_pixels) * 100
        
        has_motion = motion_percentage >= self.motion_threshold
        
        return has_motion, motion_percentage, validated_contours
    
    def _detect_motion_knn(self, frame):
        """
        Detect motion using KNN (K-Nearest Neighbors) Background Subtraction.
        Better for indoor scenes with controlled lighting.
        """
        # During learning period, just update background model without detecting
        if self.frame_count_since_reset < self.learning_frames:
            self.bg_subtractor_knn.apply(frame, learningRate=0.05)
            self.consistent_contours = []
            return False, 0.0
        
        # Apply KNN background subtraction with VERY slow learning rate
        fg_mask = self.bg_subtractor_knn.apply(frame, learningRate=0.0005)
        
        # Remove shadows (marked as 127 in the mask)
        _, fg_mask = cv2.threshold(fg_mask, 254, 255, cv2.THRESH_BINARY)
        
        # Apply VERY aggressive morphological operations to reduce noise
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11))
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel, iterations=3)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel, iterations=3)
        
        # Find contours to validate motion
        contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter contours by minimum area
        significant_contours = [c for c in contours if cv2.contourArea(c) > self.min_contour_area]
        
        if len(significant_contours) == 0:
            self.consistent_contours = []
            return False, 0.0
        
        # ADDITIONAL CHECK: Contour must be compact (not scattered noise)
        validated_contours = []
        for contour in significant_contours:
            hull = cv2.convexHull(contour)
            hull_area = cv2.contourArea(hull)
            if hull_area > 0:
                solidity = cv2.contourArea(contour) / hull_area
                if solidity > 0.4:
                    validated_contours.append(contour)
        
        if len(validated_contours) == 0:
            self.consistent_contours = []
            return False, 0.0
        
        # TEMPORAL CONSISTENCY CHECK
        if len(self.consistent_contours) > 0:
            consistent_count = 0
            for curr_contour in validated_contours:
                curr_moments = cv2.moments(curr_contour)
                if curr_moments['m00'] == 0:
                    continue
                curr_cx = int(curr_moments['m10'] / curr_moments['m00'])
                curr_cy = int(curr_moments['m01'] / curr_moments['m00'])
                
                for prev_contour in self.consistent_contours:
                    prev_moments = cv2.moments(prev_contour)
                    if prev_moments['m00'] == 0:
                        continue
                    prev_cx = int(prev_moments['m10'] / prev_moments['m00'])
                    prev_cy = int(prev_moments['m01'] / prev_moments['m00'])
                    
                    distance = np.sqrt((curr_cx - prev_cx)**2 + (curr_cy - prev_cy)**2)
                    if distance < 50:
                        consistent_count += 1
                        break
            
            consistency_ratio = consistent_count / len(validated_contours) if len(validated_contours) > 0 else 0
            if consistency_ratio < self.min_contour_consistency:
                self.consistent_contours = validated_contours
                return False, 0.0
        
        self.consistent_contours = validated_contours
        
        # Calculate percentage based on validated contours only
        total_area = sum(cv2.contourArea(c) for c in validated_contours)
        total_pixels = fg_mask.shape[0] * fg_mask.shape[1]
        motion_percentage = (total_area / total_pixels) * 100
        
        has_motion = motion_percentage >= self.motion_threshold and len(validated_contours) > 0
        
        return has_motion, motion_percentage
    
    def _detect_motion_frame_diff(self, frame):
        """
        Detect motion using simple frame differencing.
        Fast but less robust than background subtraction methods.
        """
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Apply stronger Gaussian blur to reduce noise
        gray = cv2.GaussianBlur(gray, (31, 31), 0)  # Even larger blur (was 25x25)
        
        # During learning period, just initialize
        if self.frame_count_since_reset < self.learning_frames:
            self.prev_frame = gray
            self.consistent_contours = []
            return False, 0.0
        
        # If this is the first frame, initialize
        if self.prev_frame is None:
            self.prev_frame = gray
            return False, 0.0
        
        # Compute absolute difference between current and previous frame
        frame_diff = cv2.absdiff(self.prev_frame, gray)
        
        # MUCH higher threshold for difference (was 40)
        _, thresh = cv2.threshold(frame_diff, 60, 255, cv2.THRESH_BINARY)
        
        # Apply VERY aggressive morphological operations to reduce noise
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11))
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=3)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=3)
        
        # Find contours to validate motion
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter contours by minimum area
        significant_contours = [c for c in contours if cv2.contourArea(c) > self.min_contour_area]
        
        if len(significant_contours) == 0:
            self.prev_frame = gray
            self.consistent_contours = []
            return False, 0.0
        
        # ADDITIONAL CHECK: Contour must be compact
        validated_contours = []
        for contour in significant_contours:
            hull = cv2.convexHull(contour)
            hull_area = cv2.contourArea(hull)
            if hull_area > 0:
                solidity = cv2.contourArea(contour) / hull_area
                if solidity > 0.4:
                    validated_contours.append(contour)
        
        if len(validated_contours) == 0:
            self.prev_frame = gray
            self.consistent_contours = []
            return False, 0.0
        
        # TEMPORAL CONSISTENCY CHECK
        if len(self.consistent_contours) > 0:
            consistent_count = 0
            for curr_contour in validated_contours:
                curr_moments = cv2.moments(curr_contour)
                if curr_moments['m00'] == 0:
                    continue
                curr_cx = int(curr_moments['m10'] / curr_moments['m00'])
                curr_cy = int(curr_moments['m01'] / curr_moments['m00'])
                
                for prev_contour in self.consistent_contours:
                    prev_moments = cv2.moments(prev_contour)
                    if prev_moments['m00'] == 0:
                        continue
                    prev_cx = int(prev_moments['m10'] / prev_moments['m00'])
                    prev_cy = int(prev_moments['m01'] / prev_moments['m00'])
                    
                    distance = np.sqrt((curr_cx - prev_cx)**2 + (curr_cy - prev_cy)**2)
                    if distance < 50:
                        consistent_count += 1
                        break
            
            consistency_ratio = consistent_count / len(validated_contours) if len(validated_contours) > 0 else 0
            if consistency_ratio < self.min_contour_consistency:
                self.prev_frame = gray
                self.consistent_contours = validated_contours
                return False, 0.0
        
        self.consistent_contours = validated_contours
        
        # Calculate percentage based on validated contours only
        total_area = sum(cv2.contourArea(c) for c in validated_contours)
        total_pixels = thresh.shape[0] * thresh.shape[1]
        motion_percentage = (total_area / total_pixels) * 100
        
        # Update previous frame
        self.prev_frame = gray
        
        has_motion = motion_percentage >= self.motion_threshold and len(validated_contours) > 0
        
        return has_motion, motion_percentage
    
    def _detect_motion_combined(self, frame):
        """
        Detect motion using combined methods for maximum robustness.
        Uses both MOG2 and frame differencing, requires both to agree.
        """
        # Get motion from both methods
        has_motion_mog2, motion_pct_mog2 = self._detect_motion_mog2(frame)
        has_motion_diff, motion_pct_diff = self._detect_motion_frame_diff(frame)
        
        # Both methods must agree for high confidence
        # Use the average percentage
        motion_percentage = (motion_pct_mog2 + motion_pct_diff) / 2
        has_motion = has_motion_mog2 and has_motion_diff
        
        return has_motion, motion_percentage
    
    def reset_motion_detection(self):
        """
        Reset motion detection state and background models.
        Call this when starting a new session or changing scenes.
        """
        print("[MOTION] Resetting background subtractors and motion state...")
        
        # Reset state machine
        self.motion_state = 'IDLE'
        self.candidate_frame_count = 0
        self.train_confirmation_count = 0
        self.no_motion_count = 0
        self.current_train_bbox = None
        
        # Reset frame tracking
        self.prev_frame = None
        self.frame_count_since_reset = 0
        self.frame_width = None
        self.frame_height = None
        
        # Reinitialize background subtractors with VERY conservative settings
        self.bg_subtractor_mog2 = cv2.createBackgroundSubtractorMOG2(
            history=500,
            varThreshold=100,  # Much less sensitive
            detectShadows=True
        )
        
        self.bg_subtractor_knn = cv2.createBackgroundSubtractorKNN(
            history=500,
            dist2Threshold=1200.0,  # Much less sensitive
            detectShadows=True
        )
        
        print(f"[MOTION] Motion detection reset complete. Learning background for {self.learning_frames} frames...")
        print(f"[MOTION] ULTRA-CONSERVATIVE MODE: threshold={self.motion_threshold}%, min_area={self.min_contour_area}, train_confirm_frames={self.train_confirmation_frames}")
    
    def run_live_inspection(self, session_id, session_dir, operator, use_motion_detection=False):
        """
        Run inspection on live video feed with optional motion detection.
        
        Motion Detection Modes:
        - Manual (use_motion_detection=False): Captures frames immediately
        - Auto (use_motion_detection=True): Uses motion gate to detect trains
        
        Motion Gate Logic:
        1. IDLE: Waits for motion detection
        2. DETECTING: Motion detected, confirming train presence
        3. RECORDING: Train confirmed, capturing frames
        4. AUTO-STOP: No motion for threshold period, stops recording
        """
        print(f"\n[INSPECTION] ===== run_live_inspection() CALLED =====", flush=True)
        print(f"[INSPECTION] Session: {session_id}", flush=True)
        print(f"[INSPECTION] Operator: {operator}", flush=True)
        print(f"[INSPECTION] Auto Mode: {use_motion_detection}", flush=True)
        print(f"[INSPECTION] Camera active: {self.live_video_active}", flush=True)
        print(f"[INSPECTION] =========================================\n", flush=True)
        
        # Auto-start camera if not already active
        if not self.live_video_active or self.camera is None:
            print(f"[INSPECTION] Camera not active, starting camera...", flush=True)
            try:
                from droidcam_config import DROIDCAM_URL
                video_source = DROIDCAM_URL
                print(f"[INSPECTION] Using video source: {video_source}", flush=True)
            except ImportError:
                video_source = 0
                print(f"[INSPECTION] DroidCam config not found, using camera 0", flush=True)
            
            success = self.start_live_video(video_source)
            if not success:
                print(f"[INSPECTION ERROR] Failed to start camera! Aborting inspection.", flush=True)
                self.sessions[session_id] = {
                    'frames_processed': 0,
                    'detections': 0,
                    'wagon_numbers': [],
                    'damage_detections': [],  # Store damage detections
                    'fps': 0,
                    'latency': 0,
                    'start_time': time.time(),
                    'motion_level': 0.0,
                    'motion_state': 'ERROR',
                    'error': 'Failed to connect to camera'
                }
                return
            print(f"[INSPECTION] Camera started successfully!", flush=True)
        
        if use_motion_detection:
            print(f"Starting live inspection with AUTO MOTION DETECTION (Session: {session_id})")
            print(f"  Motion Method: {self.motion_detection_method.upper()}")
            print(f"  Motion Threshold: {self.motion_threshold}% pixels")
            print(f"  Frames to Confirm Train: {self.train_confirmation_frames}")
            print(f"  No-Motion Frames to Stop: {self.no_motion_frames_to_stop}")
        else:
            print(f"Starting live inspection in MANUAL mode (Session: {session_id})")
        
        # Load models
        self._load_deblur_model()
        self._load_ocr_reader()
        
        # Reset motion detection for fresh session
        self.reset_motion_detection()
        
        # Initialize session data
        self.sessions[session_id] = {
            'frames_processed': 0,
            'detections': 0,
            'wagon_numbers': [],
            'damage_detections': [],  # Store damage detections
            'fps': 0,
            'latency': 0,
            'start_time': time.time(),
            'motion_level': 0.0,
            'motion_state': 'IDLE' if use_motion_detection else 'MANUAL'
        }
        self.stop_flags[session_id] = False
        
        # Create output directories
        frames_dir = session_dir / 'frames'
        deblurred_dir = session_dir / 'deblurred'
        wagon_dir = session_dir / 'wagon_detections'
        frames_dir.mkdir(exist_ok=True)
        deblurred_dir.mkdir(exist_ok=True)
        wagon_dir.mkdir(exist_ok=True)
        
        frame_count = 0
        recording_active = not use_motion_detection  # Manual mode starts immediately
        
        # State machine variables
        train_confirmed = False
        
        if use_motion_detection:
            print("[STATE MACHINE] Starting in IDLE state", flush=True)
            print(f"[TRAIN RULES] Width>{self.train_min_width_ratio:.0%}, Height>{self.train_min_height_ratio:.0%}, Aspect>{self.train_aspect_ratio_min}, Frames={self.train_confirmation_frames}", flush=True)
            print(f"[MOTION] Learning background for {self.learning_frames} frames...", flush=True)
        else:
            print("[MANUAL] Capturing frames immediately...", flush=True)
        
        print(f"[INSPECTION] Starting main loop for session {session_id}...", flush=True)
        
        try:
            while not self.stop_flags.get(session_id, False) and self.live_video_active:
                start_time = time.time()
                
                # Get frame from camera
                try:
                    frame = self.get_live_frame()
                    if frame is None:
                        print(f"[ERROR] get_live_frame() returned None - camera not connected?")
                        time.sleep(0.1)
                        continue
                except Exception as e:
                    print(f"[ERROR] Exception in get_live_frame(): {e}")
                    import traceback
                    traceback.print_exc()
                    time.sleep(0.1)
                    continue
                
                # ========================================
                # CRITICAL: ENFORCE FRAME CAPTURE RULE
                # ========================================
                # Motion detection runs in AUTO mode regardless of recording_active
                # But frame capture only happens when recording_active is True
                # ========================================
                
                if use_motion_detection:
                    # AUTO MODE - Always run motion detection
                    self.frame_count_since_reset += 1
                    
                    # ========================================
                    # LEARNING PHASE
                    # ========================================
                    if self.frame_count_since_reset <= self.learning_frames:
                        self.motion_state = 'LEARNING'
                        self.sessions[session_id]['motion_state'] = 'LEARNING'
                        self.sessions[session_id]['motion_level'] = 0.0
                        # Feed frames to background subtractor ONLY
                        self._detect_motion(frame)
                        if self.frame_count_since_reset == self.learning_frames:
                            print(f"[STATE MACHINE] Learning complete. Entering IDLE state.")
                            self.motion_state = 'IDLE'
                        time.sleep(0.05)
                        continue
                    
                    # ========================================
                    # MOTION DETECTION & STATE MACHINE
                    # ========================================
                    has_motion, motion_percentage, contours = self._detect_motion(frame)
                    self.sessions[session_id]['motion_level'] = round(motion_percentage, 2)
                    
                    if self.motion_state == 'IDLE':
                        # Debug: Show motion level every 10 frames in IDLE
                        if self.frame_count_since_reset % 10 == 0:
                            print(f"[IDLE] Frame {self.frame_count_since_reset}: motion_pct={motion_percentage:.2f}%, has_motion={has_motion}, threshold={self.motion_threshold}%")
                        
                        if has_motion:
                            # Motion detected - enter MOTION_CANDIDATE state
                            self.motion_state = 'MOTION_CANDIDATE'
                            self.candidate_frame_count = 1
                            self.sessions[session_id]['motion_state'] = 'MOTION_CANDIDATE'
                            print(f"[STATE MACHINE] IDLE → MOTION_CANDIDATE (motion={motion_percentage:.1f}%)")
                        else:
                            # No motion - stay in IDLE, NO FRAME CAPTURE
                            time.sleep(0.05)
                            continue
                    
                    elif self.motion_state == 'MOTION_CANDIDATE':
                        if has_motion:
                            self.candidate_frame_count += 1
                            
                            # Check if we have enough candidate frames
                            if self.candidate_frame_count >= self.motion_frames_to_candidate:
                                # STAGE 2: TRAIN CONFIRMATION
                                is_train, bbox, reason = self._validate_train_candidate(frame, contours)
                                
                                if is_train:
                                    self.train_confirmation_count += 1
                                    self.current_train_bbox = bbox
                                    
                                    if self.train_confirmation_count >= self.train_confirmation_frames:
                                        # TRAIN CONFIRMED!
                                        self.motion_state = 'INSPECTION_RUNNING'
                                        train_confirmed = True
                                        recording_active = True  # ← ENABLE FRAME CAPTURE
                                        self.sessions[session_id]['motion_state'] = 'INSPECTION_RUNNING'
                                        print(f"[STATE MACHINE] ✓✓✓ MOTION_CANDIDATE → INSPECTION_RUNNING ✓✓✓")
                                        print(f"[TRAIN CONFIRMED] {reason}")
                                        print(f"[INSPECTION] Frame capture ENABLED")
                                        # Continue to frame processing below
                                    else:
                                        print(f"[TRAIN VALIDATION] Confirming... ({self.train_confirmation_count}/{self.train_confirmation_frames}) - {reason}")
                                        time.sleep(0.05)
                                        continue
                                else:
                                    # Not a train - reset to IDLE
                                    print(f"[TRAIN VALIDATION] REJECTED: {reason}")
                                    print(f"[STATE MACHINE] MOTION_CANDIDATE → IDLE (not a train)")
                                    self.motion_state = 'IDLE'
                                    self.candidate_frame_count = 0
                                    self.train_confirmation_count = 0
                                    self.current_train_bbox = None
                                    time.sleep(0.05)
                                    continue
                            else:
                                # Still collecting candidate frames
                                time.sleep(0.05)
                                continue
                        else:
                            # Lost motion - reset to IDLE
                            print(f"[STATE MACHINE] MOTION_CANDIDATE → IDLE (motion lost)")
                            self.motion_state = 'IDLE'
                            self.candidate_frame_count = 0
                            self.train_confirmation_count = 0
                            self.sessions[session_id]['motion_state'] = 'IDLE'
                            time.sleep(0.05)
                            continue
                    
                    elif self.motion_state == 'INSPECTION_RUNNING':
                        # Simple rule: if motion drops below 20%, stop capturing
                        has_significant_motion = motion_percentage >= self.stop_motion_threshold
                        
                        if has_significant_motion:
                            self.no_motion_count = 0
                            # Log every 15 frames when train is still present
                            if self.frame_count_since_reset % 15 == 0:
                                print(f"[INSPECTION] Train present: motion={motion_percentage:.2f}% (stop_threshold={self.stop_motion_threshold}%)")
                        else:
                            self.no_motion_count += 1
                            # Log when motion drops below threshold
                            print(f"[AUTO-PAUSE] Frame {self.no_motion_count}/{self.no_motion_frames_to_stop}: motion={motion_percentage:.2f}% < {self.stop_motion_threshold}% - {'PAUSING!' if self.no_motion_count >= self.no_motion_frames_to_stop else 'counting...'}")
                        
                        # Auto-pause if no significant motion for threshold frames
                        if self.no_motion_count >= self.no_motion_frames_to_stop:
                            print(f"\n{'='*60}")
                            print(f"[STATE MACHINE] ✗✗✗ INSPECTION_RUNNING → IDLE ✗✗✗")
                            print(f"[AUTO-PAUSE] Train passed - no motion for {self.no_motion_frames_to_stop} frames")
                            print(f"[AUTO-PAUSE] Last motion: {motion_percentage:.4f}%")
                            print(f"[INSPECTION] Frame capture PAUSED - waiting for next train")
                            print(f"[AUTO-PAUSE] Video feed continues running...")
                            print(f"{'='*60}\n")
                            
                            # Pause frame capture but keep video feed running
                            recording_active = False
                            
                            # Reset state to IDLE to wait for next train
                            self.motion_state = 'IDLE'
                            self.candidate_frame_count = 0
                            self.train_confirmation_count = 0
                            self.no_motion_count = 0
                            self.current_train_bbox = None
                            self.sessions[session_id]['motion_state'] = 'IDLE'
                            
                            # Continue loop to detect next train (don't break)
                            time.sleep(0.05)
                            continue
                        # else: Continue to frame processing below
                    
                    # Debug logging every 30 frames
                    if self.frame_count_since_reset % 30 == 0:
                        print(f"[DEBUG] Frame {self.frame_count_since_reset}: state={self.motion_state}, motion={motion_percentage:.2f}%, recording={recording_active}")
                
                # ========================================
                # FRAME PROCESSING - ONLY IF RECORDING
                # ========================================
                
                # ABSOLUTE RULE: Only process frames when recording_active is True
                if not recording_active:
                    time.sleep(0.05)
                    continue
                
                # Increment processed frame counter
                frame_count += 1
                
                # Save original frame
                frame_path = frames_dir / f'frame_{frame_count:06d}.jpg'
                cv2.imwrite(str(frame_path), frame)
                
                # Enhance low light conditions first
                enhanced = self._enhance_low_light(frame)
                
                # Deblur frame for motion blur from moving trains
                deblurred = self._deblur_image(enhanced)
                
                # Apply post-processing smoothing to reduce artifacts
                deblurred = self._apply_post_smoothing(deblurred)
                
                deblurred_path = deblurred_dir / f'deblurred_{frame_count:06d}.jpg'
                cv2.imwrite(str(deblurred_path), deblurred)
                
                # Run OCR - returns wagon number and ZOOMED wagon image
                wagon_number, wagon_zoomed_image = self._detect_wagon_number_with_annotation(deblurred)
                
                # Only run damage detection if wagon is detected (train is visible)
                damage_result = None
                if wagon_number and self.damage_detector:
                    damage_result = self.damage_detector.detect_damage(deblurred)
                    
                    if damage_result and damage_result['has_damage']:
                        # Save annotated image with damage markings
                        damage_img = damage_result['annotated_image']
                        damage_img_path = wagon_dir / f'damage_{frame_count}.jpg'
                        if damage_img is not None:
                            cv2.imwrite(str(damage_img_path), damage_img)
                        
                        # Create base64 thumbnail of damage image
                        damage_base64 = None
                        try:
                            if damage_img is not None:
                                # Resize to thumbnail (320px width)
                                h, w = damage_img.shape[:2]
                                new_w = 320
                                new_h = int(h * (new_w / w))
                                damage_thumb = cv2.resize(damage_img, (new_w, new_h))
                                
                                # Encode to base64
                                success, buffer = cv2.imencode('.jpg', damage_thumb, [cv2.IMWRITE_JPEG_QUALITY, 85])
                                if success:
                                    damage_base64 = f"data:image/jpeg;base64,{base64.b64encode(buffer).decode('utf-8')}"
                        except Exception as e:
                            print(f"[DAMAGE] Error encoding damage image: {e}")
                        
                        # Save damage detection info with base64
                        self.sessions[session_id]['damage_detections'].append({
                            'frame': frame_count,
                            'damage_type': damage_result['damage_type'],
                            'damage_types': damage_result['damage_types'],
                            'confidence': damage_result['confidence'],
                            'damage_count': damage_result['damage_count'],
                            'damage_base64': damage_base64
                        })
                
                if wagon_number:
                    self.sessions[session_id]['detections'] += 1
                    self.sessions[session_id]['wagon_numbers'].append({
                        'number': wagon_number,
                        'frame': frame_count,
                        'confidence': 0.85,  # Placeholder
                        'has_damage': damage_result['has_damage'] if damage_result else False,
                        'damage_type': damage_result['damage_type'] if damage_result else None
                    })
                    
                    # Save ZOOMED wagon detection image (not full frame)
                    wagon_img_path = wagon_dir / f'wagon_{wagon_number}_{frame_count}.jpg'
                    wagon_save_img = wagon_zoomed_image if wagon_zoomed_image is not None else deblurred
                    cv2.imwrite(str(wagon_img_path), wagon_save_img)
                    print(f"  [SAVED] Wagon {wagon_number}: {wagon_save_img.shape[1]}x{wagon_save_img.shape[0]}px")
                
                # Update stats
                self.sessions[session_id]['frames_processed'] = frame_count
                self.sessions[session_id]['latency'] = int((time.time() - start_time) * 1000)
                # Calculate FPS properly - ensure it's never 0
                elapsed = time.time() - start_time
                if elapsed > 0:
                    self.sessions[session_id]['fps'] = int(1 / elapsed)
                else:
                    self.sessions[session_id]['fps'] = 1
                
                # Small delay to prevent overwhelming the system
                time.sleep(0.05)
        
        except Exception as e:
            print(f"[FATAL ERROR] Exception in inspection loop: {e}")
            import traceback
            traceback.print_exc()
        
        mode_str = "AUTO MOTION" if use_motion_detection else "MANUAL"
        print(f"[{mode_str}] Live inspection stopped (Session: {session_id}, Frames captured: {frame_count})")
    
    def run_recorded_inspection(self, session_id, session_dir, video_path, operator):
        """Run inspection on recorded video."""
        print(f"Starting recorded inspection (Session: {session_id})")
        
        # Load models
        self._load_deblur_model()
        self._load_ocr_reader()
        self._load_damage_detector()  # Load damage detector
        
        # Initialize session data
        self.sessions[session_id] = {
            'frames_processed': 0,
            'detections': 0,
            'wagon_numbers': [],
            'damage_detections': [],  # Store damage detections
            'fps': 0,
            'latency': 0,
            'start_time': time.time()
        }
        self.stop_flags[session_id] = False
        
        # Create output directories
        frames_dir = session_dir / 'frames'
        deblurred_dir = session_dir / 'deblurred'
        wagon_dir = session_dir / 'wagon_detections'
        frames_dir.mkdir(exist_ok=True)
        deblurred_dir.mkdir(exist_ok=True)
        wagon_dir.mkdir(exist_ok=True)
        
        # Open video
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"Error: Could not open video {video_path}")
            return
        
        video_fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        frame_count = 0
        
        while cap.isOpened() and not self.stop_flags.get(session_id, False):
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_count += 1
            
            # Process every 5th frame to catch more wagon numbers
            if frame_count % 5 != 0:
                continue
            
            start_time = time.time()
            
            # Save original frame
            frame_path = frames_dir / f'frame_{frame_count:06d}.jpg'
            cv2.imwrite(str(frame_path), frame)
            
            # Enhance low light conditions first
            enhanced = self._enhance_low_light(frame)
            
            # Deblur frame
            deblurred = self._deblur_image(enhanced)
            
            # Apply post-processing smoothing to reduce artifacts
            deblurred = self._apply_post_smoothing(deblurred)
            
            deblurred_path = deblurred_dir / f'deblurred_{frame_count:06d}.jpg'
            cv2.imwrite(str(deblurred_path), deblurred)
            
            # Run OCR - returns wagon number and ZOOMED wagon image
            wagon_number, wagon_zoomed_image = self._detect_wagon_number_with_annotation(deblurred)
            
            # Only run damage detection if wagon is detected (train is visible)
            damage_result = None
            if wagon_number and self.damage_detector:
                damage_result = self.damage_detector.detect_damage(deblurred)
                
                if damage_result and damage_result['has_damage']:
                    # Save annotated image with damage markings
                    damage_img = damage_result['annotated_image']
                    damage_img_path = wagon_dir / f'damage_{frame_count}.jpg'
                    if damage_img is not None:
                        cv2.imwrite(str(damage_img_path), damage_img)
                    
                    # Create base64 thumbnail of damage image
                    damage_base64 = None
                    try:
                        if damage_img is not None:
                            # Resize to thumbnail (320px width)
                            h, w = damage_img.shape[:2]
                            new_w = 320
                            new_h = int(h * (new_w / w))
                            damage_thumb = cv2.resize(damage_img, (new_w, new_h))
                            
                            # Encode to base64
                            success, buffer = cv2.imencode('.jpg', damage_thumb, [cv2.IMWRITE_JPEG_QUALITY, 85])
                            if success:
                                damage_base64 = f"data:image/jpeg;base64,{base64.b64encode(buffer).decode('utf-8')}"
                    except Exception as e:
                        print(f"[DAMAGE] Error encoding damage image: {e}")
                    
                    # Save damage detection info
                    self.sessions[session_id]['damage_detections'].append({
                        'frame': frame_count,
                        'damage_type': damage_result['damage_type'],
                        'damage_types': damage_result['damage_types'],
                        'confidence': damage_result['confidence'],
                        'damage_count': damage_result['damage_count'],
                        'damage_base64': damage_base64  # Add base64 image
                    })
            
            if wagon_number:
                self.sessions[session_id]['detections'] += 1
                
                # Save ZOOMED wagon detection image (not full frame)
                wagon_img = wagon_zoomed_image if wagon_zoomed_image is not None else deblurred
                wagon_img_path = wagon_dir / f'wagon_{wagon_number}_{frame_count}.jpg'
                cv2.imwrite(str(wagon_img_path), wagon_img)
                print(f"  [SAVED] Wagon image: {wagon_img_path.name} ({wagon_img.shape[1]}x{wagon_img.shape[0]}px)")
                
                # Create base64 thumbnail of wagon image
                wagon_base64 = None
                try:
                    # Resize to thumbnail (320px width)
                    h, w = wagon_img.shape[:2]
                    new_w = 320
                    new_h = int(h * (new_w / w))
                    wagon_thumb = cv2.resize(wagon_img, (new_w, new_h))
                    
                    # Encode to base64
                    success, buffer = cv2.imencode('.jpg', wagon_thumb, [cv2.IMWRITE_JPEG_QUALITY, 85])
                    if success:
                        wagon_base64 = f"data:image/jpeg;base64,{base64.b64encode(buffer).decode('utf-8')}"
                except Exception as e:
                    print(f"[WAGON] Error encoding wagon image: {e}")
                
                self.sessions[session_id]['wagon_numbers'].append({
                    'number': wagon_number,
                    'frame': frame_count,
                    'confidence': 0.85,
                    'timestamp': time.time(),
                    'has_damage': damage_result['has_damage'] if damage_result else False,
                    'damage_type': damage_result['damage_type'] if damage_result else None,
                    'wagon_base64': wagon_base64  # Add base64 image
                })
                
                print(f"  [Detection] Wagon {wagon_number} at frame {frame_count}")
            
            # Update stats
            self.sessions[session_id]['frames_processed'] = frame_count
            process_time = time.time() - start_time
            self.sessions[session_id]['latency'] = int(process_time * 1000)
            self.sessions[session_id]['fps'] = int(1 / process_time) if process_time > 0 else 0
            
            # Progress update every 30 frames
            if frame_count % 30 == 0:
                print(f"  Progress: {frame_count}/{total_frames} frames, {self.sessions[session_id]['detections']} detections")
        
        cap.release()
        
        # Mark session as completed
        self.sessions[session_id]['completed'] = True
        self.sessions[session_id]['end_time'] = time.time()
        
        print(f"Recorded inspection completed (Session: {session_id})")
    
    def stop_inspection(self, session_id):
        """Stop running inspection."""
        if session_id in self.stop_flags:
            self.stop_flags[session_id] = True
            print(f"Stop signal sent for session {session_id}")
    
    def get_inspection_status(self, session_id, sessions_folder=None):
        """Get current status of inspection."""
        if session_id not in self.sessions:
            return None
        
        session = self.sessions[session_id]
        
        # Check if completed
        is_completed = session.get('completed', False)
        
        # Get all deblurred frames from the session directory
        deblurred_frames = []
        deblurred_thumbnails = []  # Base64 encoded thumbnails
        original_thumbnails = []  # Base64 encoded original frames
        
        if sessions_folder:
            from pathlib import Path
            
            deblurred_dir = Path(sessions_folder) / session_id / 'deblurred'
            frames_dir = Path(sessions_folder) / session_id / 'frames'
            
            if deblurred_dir.exists():
                # Get all frames (no limit)
                deblurred_files = sorted(deblurred_dir.glob('*.jpg'))
                print(f"[THUMBNAILS] Found {len(deblurred_files)} frames to process")
                
                for img_file in deblurred_files:
                    # Add path for reference
                    deblurred_frames.append(f'/api/session/{session_id}/image/{img_file.name}')
                    
                    # Generate base64 thumbnail
                    try:
                        img = cv2.imread(str(img_file))
                        if img is not None:
                            # Resize to thumbnail (320px width)
                            h, w = img.shape[:2]
                            new_w = 320
                            new_h = int(h * (new_w / w))
                            thumbnail = cv2.resize(img, (new_w, new_h))
                            
                            # Encode to base64
                            success, buffer = cv2.imencode('.jpg', thumbnail, [cv2.IMWRITE_JPEG_QUALITY, 85])
                            if success:
                                thumbnail_b64 = f"data:image/jpeg;base64,{base64.b64encode(buffer).decode('utf-8')}"
                                deblurred_thumbnails.append(thumbnail_b64)
                                print(f"[THUMBNAILS] Generated deblurred thumbnail {len(deblurred_thumbnails)}")
                            else:
                                print(f"[THUMBNAILS] Failed to encode {img_file.name}")
                            
                            # Also get corresponding original frame
                            frame_name = img_file.name.replace('deblurred_', 'frame_')
                            original_path = frames_dir / frame_name
                            if original_path.exists():
                                orig_img = cv2.imread(str(original_path))
                                if orig_img is not None:
                                    orig_thumbnail = cv2.resize(orig_img, (new_w, new_h))
                                    success, orig_buffer = cv2.imencode('.jpg', orig_thumbnail, [cv2.IMWRITE_JPEG_QUALITY, 85])
                                    if success:
                                        orig_b64 = f"data:image/jpeg;base64,{base64.b64encode(orig_buffer).decode('utf-8')}"
                                        original_thumbnails.append(orig_b64)
                                        print(f"[THUMBNAILS] Generated original thumbnail {len(original_thumbnails)}")
                        else:
                            print(f"[THUMBNAILS] Could not read {img_file.name}")
                    except Exception as e:
                        print(f"[THUMBNAILS] Error generating thumbnail for {img_file.name}: {e}")
                        import traceback
                        traceback.print_exc()
        
        return {
            'frames_processed': session.get('frames_processed', 0),
            'detections': session.get('detections', 0),
            'wagon_numbers': session.get('wagon_numbers', []),
            'damage_detections': session.get('damage_detections', []),  # Add damage detections
            'deblurred_frames': deblurred_frames,
            'deblurred_thumbnails': deblurred_thumbnails,  # Base64 thumbnails
            'original_thumbnails': original_thumbnails,  # Base64 original frames
            'fps': session.get('fps', 0),
            'latency': session.get('latency', 0),
            'completed': is_completed,
            'motion_state': session.get('motion_state', 'IDLE'),
            'motion_level': session.get('motion_level', 0),
            'train_confirmed': session.get('motion_state') in ['TRAIN_CONFIRMED', 'INSPECTION_RUNNING']
        }
    
    def get_session_results(self, session_id):
        """Get final results for session."""
        if session_id not in self.sessions:
            return {}
        
        session = self.sessions[session_id]
        duration = int(time.time() - session['start_time'])
        
        unique_wagons = list(set([w['number'] for w in session['wagon_numbers']]))
        
        return {
            'frames_processed': session['frames_processed'],
            'wagons_detected': len(unique_wagons),
            'readable': len(unique_wagons),
            'unreadable': 0,
            'duration': duration,
            'wagon_numbers': unique_wagons,
            'damage_detections': session.get('damage_detections', []),  # Add damage detections
            'total_damages': len(session.get('damage_detections', []))
        }
    
    # ====================================================
    # IMAGE PROCESSING
    # ====================================================
    
    def process_single_image(self, image_path):
        """Process single image for deblurring and wagon detection."""
        print(f"Processing image: {image_path}")
        
        # Load models
        self._load_deblur_model()
        self._load_ocr_reader()
        self._load_damage_detector()  # Load damage detector
        
        # Read image
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Could not read image: {image_path}")
        
        start_time = time.time()
        
        # Enhance low light conditions first
        enhanced = self._enhance_low_light(image)
        
        # Deblur image
        deblurred = self._deblur_image(enhanced)
        
        # Detect wagon number with annotation
        wagon_number, annotated_image = self._detect_wagon_number_with_annotation(deblurred)
        
        # Run damage detection
        damage_result = None
        damage_path = None
        damage_base64 = None
        if self.damage_detector:
            damage_result = self.damage_detector.detect_damage(deblurred)
            
            # Save damage-annotated image if damage detected
            if damage_result and damage_result['has_damage'] and damage_result['annotated_image'] is not None:
                damage_path = str(Path(image_path).parent / f"damage_{Path(image_path).stem}.jpg")
                cv2.imwrite(damage_path, damage_result['annotated_image'])
                # Convert to base64 for response
                _, buffer = cv2.imencode('.jpg', damage_result['annotated_image'])
                damage_base64 = f"data:image/jpeg;base64,{base64.b64encode(buffer).decode('utf-8')}"
                print(f"[DAMAGE] Detected {damage_result['damage_count']} damage(s): {damage_result['damage_type']}")
        
        processing_time = int((time.time() - start_time) * 1000)
        
        # Apply post-processing smoothing to reduce artifacts
        deblurred = self._apply_post_smoothing(deblurred)
        
        # Save deblurred image
        output_path = str(Path(image_path).parent / f"deblurred_{Path(image_path).name}")
        cv2.imwrite(output_path, deblurred)
        
        # Save wagon detection image with annotation if detected
        wagon_path = None
        wagon_base64 = None
        if wagon_number and annotated_image is not None:
            wagon_path = str(Path(image_path).parent / f"wagon_{wagon_number}_{Path(image_path).stem}.jpg")
            cv2.imwrite(wagon_path, annotated_image)
            # Convert wagon image to base64
            _, buffer = cv2.imencode('.jpg', annotated_image)
            wagon_base64 = f"data:image/jpeg;base64,{base64.b64encode(buffer).decode('utf-8')}"
            print(f"[OCR] Detected wagon number: {wagon_number}")
        
        # Convert to base64 for response
        _, buffer = cv2.imencode('.jpg', deblurred)
        deblurred_base64 = f"data:image/jpeg;base64,{base64.b64encode(buffer).decode('utf-8')}"
        
        return {
            'original_path': image_path,
            'deblurred_path': output_path,
            'deblurred_base64': deblurred_base64,
            'processing_time': processing_time,
            'image_size': f"{image.shape[1]}x{image.shape[0]}",
            'wagon_number': wagon_number,
            'wagon_path': wagon_path,
            'wagon_base64': wagon_base64,
            'damage_detected': damage_result['has_damage'] if damage_result else False,
            'damage_type': damage_result['damage_type'] if damage_result else None,
            'damage_confidence': damage_result['confidence'] if damage_result else 0.0,
            'damage_count': damage_result['damage_count'] if damage_result else 0,
            'damage_path': damage_path,
            'damage_base64': damage_base64
        }
    
    # ====================================================
    # HELPER FUNCTIONS
    # ====================================================
    
    def _deblur_image(self, image):
        """Apply deblurring to image - matches process_railway_video.py exactly."""
        if self.deblur_model is None:
            print("WARNING: No deblur model loaded, returning original image")
            return image
        
        try:
            # Step 1: Check if image is blurry using Laplacian variance
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            
            # Threshold for blur detection
            # Higher variance = sharper image
            # Lower variance = more blur (motion blur from moving train)
            blur_threshold = 150
            
            if laplacian_var > blur_threshold:
                print(f"[SKIP DEBLUR] Image is already clear (sharpness: {laplacian_var:.2f})")
                return image
            
            print(f"[DEBLUR] Image is blurry (sharpness: {laplacian_var:.2f}), applying deblurring...")
            
            # Get original dimensions
            h, w = image.shape[:2]
            
            # Pad to multiple of 16 (MIMOUNetPlus requirement)
            pad_h = (16 - h % 16) % 16
            pad_w = (16 - w % 16) % 16
            
            # Pad with reflection
            padded = cv2.copyMakeBorder(image, 0, pad_h, 0, pad_w, cv2.BORDER_REFLECT)
            
            # Convert to tensor: [H, W, C] -> [C, H, W] -> [1, C, H, W]
            # Normalize to [0, 1] by dividing by 255.0
            img_tensor = torch.from_numpy(padded).float().permute(2, 0, 1).unsqueeze(0) / 255.0
            img_tensor = img_tensor.to(self.device)
            
            # Run model
            with torch.no_grad():
                outputs = self.deblur_model(img_tensor)
                # Handle multi-scale output
                output = outputs[0] if isinstance(outputs, (list, tuple)) else outputs
            
            # Convert back to image: [1, C, H, W] -> [C, H, W] -> [H, W, C]
            output_img = output.squeeze(0).permute(1, 2, 0).cpu().numpy()
            
            # Denormalize: [0, 1] -> [0, 255]
            output_img = np.clip(output_img * 255.0, 0, 255).astype(np.uint8)
            
            # Remove padding
            output_img = output_img[:h, :w]
            
            print(f"[DEBLUR] ✓ Deblurring complete")
            return output_img
            
        except Exception as e:
            print(f"ERROR in deblurring: {e}")
            import traceback
            traceback.print_exc()
            return image
    
    def _enhance_low_light(self, image):
        """Enhance low-light/dark images using multiple techniques."""
        try:
            # Convert to LAB color space for better brightness control
            lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            
            # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization) to L channel
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            l_enhanced = clahe.apply(l)
            
            # Merge back and convert to BGR
            lab_enhanced = cv2.merge([l_enhanced, a, b])
            enhanced = cv2.cvtColor(lab_enhanced, cv2.COLOR_LAB2BGR)
            
            # Additional gamma correction for very dark images
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            mean_brightness = np.mean(gray)
            
            if mean_brightness < 50:  # Very dark
                gamma = 1.5  # Brighten more
            elif mean_brightness < 80:  # Moderately dark
                gamma = 1.2
            else:
                gamma = 1.0
            
            if gamma != 1.0:
                # Build a lookup table mapping pixel values [0, 255] to adjusted gamma values
                inv_gamma = 1.0 / gamma
                table = np.array([((i / 255.0) ** inv_gamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
                enhanced = cv2.LUT(enhanced, table)
                print(f"[LOW-LIGHT] Applied gamma correction: {gamma}")
            
            print(f"[LOW-LIGHT] Enhanced brightness from {mean_brightness:.2f} to {np.mean(cv2.cvtColor(enhanced, cv2.COLOR_BGR2GRAY)):.2f}")
            return enhanced
            
        except Exception as e:
            print(f"Error in low-light enhancement: {e}")
            return image
    
    def _apply_post_smoothing(self, image, strength='light'):
        """
        Apply post-processing smoothing to deblurred images.
        Reduces artifacts while preserving text sharpness.
        
        Args:
            image: Deblurred image (BGR)
            strength: 'light', 'medium', or 'strong'
        
        Returns:
            Smoothed image
        """
        try:
            # Bilateral filter - preserves edges while smoothing
            # Perfect for deblurred images with text
            
            if strength == 'light':
                # Light smoothing - minimal artifact reduction
                d = 5  # Diameter of pixel neighborhood
                sigmaColor = 30  # Color space sigma
                sigmaSpace = 30  # Coordinate space sigma
            elif strength == 'medium':
                # Medium smoothing - balanced
                d = 7
                sigmaColor = 50
                sigmaSpace = 50
            elif strength == 'strong':
                # Strong smoothing - maximum artifact reduction
                d = 9
                sigmaColor = 75
                sigmaSpace = 75
            else:
                # Default to light
                d = 5
                sigmaColor = 30
                sigmaSpace = 30
            
            # Apply bilateral filter (edge-preserving smoothing)
            smoothed = cv2.bilateralFilter(image, d, sigmaColor, sigmaSpace)
            
            # Optional: Slight sharpening to recover text clarity
            # Create sharpening kernel
            kernel_sharpen = np.array([
                [-0.5, -0.5, -0.5],
                [-0.5,  5.0, -0.5],
                [-0.5, -0.5, -0.5]
            ])
            
            # Apply subtle sharpening (only for light/medium)
            if strength in ['light', 'medium']:
                sharpened = cv2.filter2D(smoothed, -1, kernel_sharpen)
                # Blend: 70% smoothed + 30% sharpened
                smoothed = cv2.addWeighted(smoothed, 0.7, sharpened, 0.3, 0)
            
            return smoothed
            
        except Exception as e:
            print(f"Error in post-smoothing: {e}")
            return image
    
    def _detect_wagon_number(self, image):
        """Detect wagon number from image using OCR with enhanced preprocessing."""
        wagon_number, _ = self._detect_wagon_number_with_annotation(image)
        return wagon_number
    
    def _detect_wagon_number_with_annotation(self, image):
        """Detect wagon number, zoom to region, deblur, and return zoomed image."""
        if self.ocr_reader is None:
            return None, None
        
        try:
            import re
            
            # Pattern for wagon numbers - support 6-10 digit numbers and alphanumeric
            pattern = r'[A-Z]{1,3}[-\s]?\d{4,9}|\d{6,10}'
            
            detected_numbers = []
            annotated_image = image.copy()
            wagon_number_region = None  # Store the zoomed wagon number region
            
            # Check if image is dark and enhance for OCR
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            mean_brightness = np.mean(gray)
            
            if mean_brightness < 100:
                print(f"[OCR] Dark image detected (brightness: {mean_brightness:.2f}), applying extra enhancement")
                # Apply stronger enhancement for OCR
                lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
                l, a, b = cv2.split(lab)
                clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(8, 8))
                l_enhanced = clahe.apply(l)
                lab_enhanced = cv2.merge([l_enhanced, a, b])
                image_for_ocr = cv2.cvtColor(lab_enhanced, cv2.COLOR_LAB2BGR)
            else:
                image_for_ocr = image.copy()
            
            # Strategy 1: Direct OCR on enhanced image
            results = self.ocr_reader.readtext(image_for_ocr)
            
            # Get image dimensions for position filtering
            img_height, img_width = image.shape[:2]
            
            for detection in results:
                bbox, text, confidence = detection[0], detection[1].strip().upper(), detection[2]
                
                # FILTER WATERMARKS: Check position in image
                y_coords = [point[1] for point in bbox]
                x_coords = [point[0] for point in bbox]
                bbox_top = min(y_coords)
                bbox_bottom = max(y_coords)
                bbox_left = min(x_coords)
                bbox_right = max(x_coords)
                bbox_center_y = (bbox_top + bbox_bottom) / 2
                bbox_center_x = (bbox_left + bbox_right) / 2
                
                # Skip watermarks at bottom 25% of image
                if bbox_center_y > img_height * 0.75:
                    print(f"  [FILTER] Skipping watermark at bottom: '{text}' (y={bbox_center_y:.0f}/{img_height})")
                    continue
                
                # Skip watermarks at top 10% of image (often logos/timestamps)
                if bbox_center_y < img_height * 0.10:
                    print(f"  [FILTER] Skipping watermark at top: '{text}' (y={bbox_center_y:.0f}/{img_height})")
                    continue
                
                # Skip text at extreme left/right edges (5% margin) - less strict
                if bbox_center_x < img_width * 0.05 or bbox_center_x > img_width * 0.95:
                    print(f"  [FILTER] Skipping edge text: '{text}' (x={bbox_center_x:.0f}/{img_width})")
                    continue
                
                # Additional check: Skip very small text (likely noise, not wagon numbers)
                bbox_width = max(x_coords) - min(x_coords)
                bbox_height = max(y_coords) - min(y_coords)
                if bbox_width < 50 or bbox_height < 20:
                    print(f"  [FILTER] Skipping small text: '{text}' (size={bbox_width:.0f}x{bbox_height:.0f})")
                    continue
                
                # Draw all detected text boxes for debugging
                pts = np.array(bbox, np.int32).reshape((-1, 1, 2))
                cv2.polylines(annotated_image, [pts], True, (0, 255, 255), 2)  # Yellow boxes
                
                # Check if matches wagon number pattern
                match = re.search(pattern, text)
                if match and confidence > 0.3:  # Lower confidence threshold
                    wagon_num = match.group().replace(' ', '-')
                    if '-' not in wagon_num and len(wagon_num) > 2:
                        # Format if not already formatted
                        if any(c.isalpha() for c in wagon_num[:3]):
                            # Has letters at start
                            letters = ''.join(c for c in wagon_num if c.isalpha())
                            digits = ''.join(c for c in wagon_num if c.isdigit())
                            wagon_num = f"{letters}-{digits}"
                    
                    detected_numbers.append((wagon_num, confidence, bbox))
                    print(f"  [OCR] Found: {wagon_num} (confidence: {confidence:.2f})")
                    
                    # CROP EXACTLY TO THE OCR BOUNDING BOX
                    # Get bounding box coordinates
                    x_coords = [point[0] for point in bbox]
                    y_coords = [point[1] for point in bbox]
                    x_min, x_max = int(min(x_coords)), int(max(x_coords))
                    y_min, y_max = int(min(y_coords)), int(max(y_coords))
                    
                    # Add minimal padding (10 pixels) to avoid cutting edges
                    h, w = image.shape[:2]
                    padding = 10
                    
                    x_min = max(0, x_min - padding)
                    x_max = min(w, x_max + padding)
                    y_min = max(0, y_min - padding)
                    y_max = min(h, y_max + padding)
                    
                    # Crop to wagon number region ONLY
                    wagon_region = image[y_min:y_max, x_min:x_max]
                    
                    # DEBLUR THE ZOOMED REGION
                    print(f"  [ZOOM] Cropped wagon number region: {wagon_region.shape[1]}x{wagon_region.shape[0]} pixels")
                    wagon_region_deblurred = self._deblur_image(wagon_region)
                    
                    # Calculate bbox position relative to cropped region
                    bbox_local = [(int(x - x_min), int(y - y_min)) for x, y in bbox]
                    pts_local = np.array(bbox_local, np.int32).reshape((-1, 1, 2))
                    
                    # Draw wagon number box in GREEN on the ZOOMED region
                    wagon_number_region = wagon_region_deblurred.copy()
                    cv2.polylines(wagon_number_region, [pts_local], True, (0, 255, 0), 3)
                    
                    # Add text label above the box
                    text_y = max(10, bbox_local[0][1] - 10)
                    cv2.putText(wagon_number_region, wagon_num, (int(bbox_local[0][0]), text_y), 
                               cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)
                    
                    # RETURN IMMEDIATELY with zoomed image
                    print(f"  [ZOOM] Returning zoomed+deblurred wagon number region")
                    return wagon_num, wagon_number_region
            
            # Strategy 2: Enhanced contrast preprocessing with adaptive thresholding
            gray_enhanced = cv2.cvtColor(image_for_ocr, cv2.COLOR_BGR2GRAY)
            
            # Apply bilateral filter to reduce noise while keeping edges
            bilateral = cv2.bilateralFilter(gray_enhanced, 9, 75, 75)
            
            # Adaptive thresholding
            adaptive_thresh = cv2.adaptiveThreshold(bilateral, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                                   cv2.THRESH_BINARY, 11, 2)
            
            results_adaptive = self.ocr_reader.readtext(adaptive_thresh)
            for detection in results_adaptive:
                bbox, text, confidence = detection[0], detection[1].strip().upper(), detection[2]
                
                # Apply same position filtering
                y_coords = [point[1] for point in bbox]
                x_coords = [point[0] for point in bbox]
                bbox_center_y = (min(y_coords) + max(y_coords)) / 2
                bbox_center_x = (min(x_coords) + max(x_coords)) / 2
                
                if bbox_center_y > img_height * 0.75 or bbox_center_y < img_height * 0.10:
                    continue
                if bbox_center_x < img_width * 0.05 or bbox_center_x > img_width * 0.95:
                    continue
                bbox_width = max(x_coords) - min(x_coords)
                bbox_height = max(y_coords) - min(y_coords)
                if bbox_width < 50 or bbox_height < 20:
                    continue
                
                match = re.search(pattern, text)
                if match and confidence > 0.3:
                    wagon_num = match.group().replace(' ', '-')
                    if '-' not in wagon_num:
                        wagon_num = wagon_num[:2] + '-' + wagon_num[2:]
                    detected_numbers.append((wagon_num, confidence, bbox))
                    print(f"  [OCR Adaptive] Found: {wagon_num} (confidence: {confidence:.2f})")
                    
                    # ZOOM AND DEBLUR
                    x_min, x_max = int(min(x_coords)), int(max(x_coords))
                    y_min, y_max = int(min(y_coords)), int(max(y_coords))
                    padding = 10
                    x_min = max(0, x_min - padding)
                    x_max = min(img_width, x_max + padding)
                    y_min = max(0, y_min - padding)
                    y_max = min(img_height, y_max + padding)
                    
                    wagon_region = image[y_min:y_max, x_min:x_max]
                    wagon_region_deblurred = self._deblur_image(wagon_region)
                    
                    bbox_local = [(int(x - x_min), int(y - y_min)) for x, y in bbox]
                    pts_local = np.array(bbox_local, np.int32).reshape((-1, 1, 2))
                    
                    wagon_number_region = wagon_region_deblurred.copy()
                    cv2.polylines(wagon_number_region, [pts_local], True, (0, 255, 0), 3)
                    cv2.putText(wagon_number_region, wagon_num, (int(bbox_local[0][0]), max(10, bbox_local[0][1] - 10)), 
                               cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)
                    
                    return wagon_num, wagon_number_region
            
            # Strategy 3: Otsu's thresholding
            _, thresh = cv2.threshold(gray_enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            results_thresh = self.ocr_reader.readtext(thresh)
            for detection in results_thresh:
                bbox, text, confidence = detection[0], detection[1].strip().upper(), detection[2]
                
                # Apply same position filtering
                y_coords = [point[1] for point in bbox]
                x_coords = [point[0] for point in bbox]
                bbox_center_y = (min(y_coords) + max(y_coords)) / 2
                bbox_center_x = (min(x_coords) + max(x_coords)) / 2
                
                if bbox_center_y > img_height * 0.75 or bbox_center_y < img_height * 0.10:
                    continue
                if bbox_center_x < img_width * 0.05 or bbox_center_x > img_width * 0.95:
                    continue
                bbox_width = max(x_coords) - min(x_coords)
                bbox_height = max(y_coords) - min(y_coords)
                if bbox_width < 50 or bbox_height < 20:
                    continue
                
                match = re.search(pattern, text)
                if match and confidence > 0.3:
                    wagon_num = match.group().replace(' ', '-')
                    if '-' not in wagon_num:
                        wagon_num = wagon_num[:2] + '-' + wagon_num[2:]
                    detected_numbers.append((wagon_num, confidence, bbox))
                    print(f"  [OCR Otsu] Found: {wagon_num} (confidence: {confidence:.2f})")
                    
                    # ZOOM AND DEBLUR
                    x_min, x_max = int(min(x_coords)), int(max(x_coords))
                    y_min, y_max = int(min(y_coords)), int(max(y_coords))
                    padding = 10
                    x_min = max(0, x_min - padding)
                    x_max = min(img_width, x_max + padding)
                    y_min = max(0, y_min - padding)
                    y_max = min(img_height, y_max + padding)
                    
                    wagon_region = image[y_min:y_max, x_min:x_max]
                    wagon_region_deblurred = self._deblur_image(wagon_region)
                    
                    bbox_local = [(int(x - x_min), int(y - y_min)) for x, y in bbox]
                    pts_local = np.array(bbox_local, np.int32).reshape((-1, 1, 2))
                    
                    wagon_number_region = wagon_region_deblurred.copy()
                    cv2.polylines(wagon_number_region, [pts_local], True, (0, 255, 0), 3)
                    cv2.putText(wagon_number_region, wagon_num, (int(bbox_local[0][0]), max(10, bbox_local[0][1] - 10)), 
                               cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)
                    
                    return wagon_num, wagon_number_region
            
            # Strategy 4: Inverted image (white text on black background)
            inverted = cv2.bitwise_not(gray_enhanced)
            
            results_inverted = self.ocr_reader.readtext(inverted)
            for detection in results_inverted:
                bbox, text, confidence = detection[0], detection[1].strip().upper(), detection[2]
                
                # Apply same position filtering
                y_coords = [point[1] for point in bbox]
                x_coords = [point[0] for point in bbox]
                bbox_center_y = (min(y_coords) + max(y_coords)) / 2
                bbox_center_x = (min(x_coords) + max(x_coords)) / 2
                
                if bbox_center_y > img_height * 0.75 or bbox_center_y < img_height * 0.10:
                    continue
                if bbox_center_x < img_width * 0.05 or bbox_center_x > img_width * 0.95:
                    continue
                bbox_width = max(x_coords) - min(x_coords)
                bbox_height = max(y_coords) - min(y_coords)
                if bbox_width < 50 or bbox_height < 20:
                    continue
                
                match = re.search(pattern, text)
                if match and confidence > 0.3:
                    wagon_num = match.group().replace(' ', '-')
                    if '-' not in wagon_num:
                        wagon_num = wagon_num[:2] + '-' + wagon_num[2:]
                    detected_numbers.append((wagon_num, confidence, bbox))
                    print(f"  [OCR Inverted] Found: {wagon_num} (confidence: {confidence:.2f})")
            
            # Strategy 5: Morphological operations to separate text
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            morph = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
            
            results_morph = self.ocr_reader.readtext(morph)
            for detection in results_morph:
                bbox, text, confidence = detection[0], detection[1].strip().upper(), detection[2]
                
                # Apply same position filtering
                y_coords = [point[1] for point in bbox]
                x_coords = [point[0] for point in bbox]
                bbox_center_y = (min(y_coords) + max(y_coords)) / 2
                bbox_center_x = (min(x_coords) + max(x_coords)) / 2
                
                if bbox_center_y > img_height * 0.75 or bbox_center_y < img_height * 0.10:
                    continue
                if bbox_center_x < img_width * 0.05 or bbox_center_x > img_width * 0.95:
                    continue
                bbox_width = max(x_coords) - min(x_coords)
                bbox_height = max(y_coords) - min(y_coords)
                if bbox_width < 50 or bbox_height < 20:
                    continue
                
                match = re.search(pattern, text)
                
                match = re.search(pattern, text)
                if match and confidence > 0.3:
                    wagon_num = match.group().replace(' ', '-')
                    if '-' not in wagon_num:
                        wagon_num = wagon_num[:2] + '-' + wagon_num[2:]
                    detected_numbers.append((wagon_num, confidence, bbox))
                    print(f"  [OCR Morph] Found: {wagon_num} (confidence: {confidence:.2f})")
                    
                    # ZOOM AND DEBLUR
                    x_min, x_max = int(min(x_coords)), int(max(x_coords))
                    y_min, y_max = int(min(y_coords)), int(max(y_coords))
                    padding = 10
                    x_min = max(0, x_min - padding)
                    x_max = min(img_width, x_max + padding)
                    y_min = max(0, y_min - padding)
                    y_max = min(img_height, y_max + padding)
                    
                    wagon_region = image[y_min:y_max, x_min:x_max]
                    wagon_region_deblurred = self._deblur_image(wagon_region)
                    
                    bbox_local = [(int(x - x_min), int(y - y_min)) for x, y in bbox]
                    pts_local = np.array(bbox_local, np.int32).reshape((-1, 1, 2))
                    
                    wagon_number_region = wagon_region_deblurred.copy()
                    cv2.polylines(wagon_number_region, [pts_local], True, (0, 255, 0), 3)
                    cv2.putText(wagon_number_region, wagon_num, (int(bbox_local[0][0]), max(10, bbox_local[0][1] - 10)), 
                               cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)
                    
                    return wagon_num, wagon_number_region
            
            # If any wagon numbers detected, return the one with highest confidence
            if detected_numbers:
                # Sort by confidence
                detected_numbers.sort(key=lambda x: x[1], reverse=True)
                best_match = detected_numbers[0]
                print(f"  [FINAL] Selected: {best_match[0]} (confidence: {best_match[1]:.2f})")
                return best_match[0], annotated_image
            
            # If no clear wagon number, try to extract any text that looks like wagon number
            all_text = ' '.join([d[1].strip().upper() for d in results])
            match = re.search(pattern, all_text)
            if match:
                wagon_num = match.group().replace(' ', '-')
                if '-' not in wagon_num:
                    wagon_num = wagon_num[:2] + '-' + wagon_num[2:]
                print(f"  [FALLBACK] Found: {wagon_num}")
                return wagon_num, annotated_image
            
            return None, None
            
        except Exception as e:
            print(f"Error in OCR: {e}")
            return None, None


