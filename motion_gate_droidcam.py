"""
Robust Motion Gate Script for Railway Wagon Inspection
========================================================

Features:
- Reads video from DroidCam (IP Webcam)
- OpenCV Background Subtraction for motion detection
- Motion Gate: IDLE until train detected, then ACTIVE
- Saves frames during ACTIVE mode
- Placeholder for MIMO deblurring integration

Author: Railway Inspection System
Date: December 27, 2025
"""

import cv2
import numpy as np
from pathlib import Path
from datetime import datetime
import time

# =====================================================
# CONFIGURATION
# =====================================================

# DroidCam Video Source
DROIDCAM_URL = "http://192.168.1.6:4747/video"  # Change to your DroidCam IP

# Motion Detection Settings - ULTRA CONSERVATIVE
MOTION_THRESHOLD = 35.0  # % of pixels that must change (VERY HIGH - prevents false positives)
MIN_CONTOUR_AREA = 15000  # Minimum area of moving object (TRIPLED - only large objects)
FRAMES_TO_CONFIRM_TRAIN = 25  # Consecutive motion frames to activate (INCREASED)
FRAMES_NO_MOTION_TO_STOP = 60  # Consecutive no-motion frames to deactivate
LEARNING_FRAMES = 60  # Frames to learn background before detecting (DOUBLED)

# Background Subtractor Settings
BG_HISTORY = 500  # Number of frames for background model (INCREASED for stability)
BG_VAR_THRESHOLD = 100  # Sensitivity (DOUBLED - much less sensitive)
BG_LEARNING_RATE = 0.0005  # Very slow adaptation to avoid false positives

# Additional validation
MIN_CONTOUR_SOLIDITY = 0.4  # Minimum solidity (compactness) of contours
MIN_CONTOUR_CONSISTENCY = 0.7  # 70% of contours must persist across frames

# Output Settings
OUTPUT_FOLDER = Path("motion_gate_output")
SAVE_FRAMES = True  # Set to False to just detect without saving

# Display Settings
SHOW_PREVIEW = True  # Show live video window
SHOW_MOTION_MASK = True  # Show motion detection visualization

# =====================================================
# MOTION GATE CLASS
# =====================================================

class MotionGate:
    """
    Motion Gate Controller
    
    States:
    - IDLE: No motion detected, not capturing
    - LEARNING: Building background model (first N frames)
    - DETECTING: Motion detected, confirming train presence
    - ACTIVE: Train confirmed, capturing frames
    """
    
    def __init__(self):
        """Initialize motion gate with OpenCV background subtractor."""
        print("=" * 60)
        print("MOTION GATE - Railway Wagon Inspection")
        print("=" * 60)
        
        # Create background subtractor (MOG2)
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=BG_HISTORY,
            varThreshold=BG_VAR_THRESHOLD,
            detectShadows=True
        )
        
        # State tracking
        self.state = "LEARNING"
        self.frame_count = 0
        self.motion_frame_count = 0
        self.no_motion_frame_count = 0
        self.captured_frames = 0
        
        # Create output directory
        if SAVE_FRAMES:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.session_folder = OUTPUT_FOLDER / f"session_{timestamp}"
            self.frames_folder = self.session_folder / "frames"
            self.frames_folder.mkdir(parents=True, exist_ok=True)
            print(f"✓ Output folder: {self.frames_folder}")
        
        print(f"✓ Motion Threshold: {MOTION_THRESHOLD}%")
        print(f"✓ Min Contour Area: {MIN_CONTOUR_AREA} pixels")
        print(f"✓ Frames to Confirm: {FRAMES_TO_CONFIRM_TRAIN}")
        print(f"✓ Frames to Stop: {FRAMES_NO_MOTION_TO_STOP}")
        print("=" * 60)
    
    def detect_motion(self, frame):
        """
        Detect motion in frame using OpenCV Background Subtraction.
        
        Args:
            frame: BGR image from camera
            
        Returns:
            (has_motion, motion_percentage, fg_mask)
        """
        # During learning phase, just update background model
        if self.frame_count < LEARNING_FRAMES:
            fg_mask = self.bg_subtractor.apply(frame, learningRate=0.1)  # Fast learning
            return False, 0.0, fg_mask
        
        # Apply background subtraction with slow learning rate
        fg_mask = self.bg_subtractor.apply(frame, learningRate=BG_LEARNING_RATE)
        
        # Remove shadows (value 127) - keep only foreground (255)
        _, fg_mask = cv2.threshold(fg_mask, 250, 255, cv2.THRESH_BINARY)
        
        # Morphological operations to reduce noise
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel, iterations=2)  # Remove small noise
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel, iterations=2)  # Fill holes
        
        # Find contours (connected components)
        contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter by minimum area to remove small noise
        significant_contours = [c for c in contours if cv2.contourArea(c) > MIN_CONTOUR_AREA]
        
        # No significant motion if no large contours
        if len(significant_contours) == 0:
            return False, 0.0, fg_mask
        
        # Calculate total area of moving objects
        total_area = sum(cv2.contourArea(c) for c in significant_contours)
        total_pixels = fg_mask.shape[0] * fg_mask.shape[1]
        motion_percentage = (total_area / total_pixels) * 100
        
        # Motion detected if percentage exceeds threshold
        has_motion = motion_percentage >= MOTION_THRESHOLD
        
        return has_motion, motion_percentage, fg_mask
    
    def update_state(self, has_motion, motion_percentage):
        """
        Update motion gate state based on motion detection.
        
        State Machine:
        LEARNING -> IDLE -> DETECTING -> ACTIVE -> IDLE (cycle)
        """
        # LEARNING STATE: Building background model
        if self.state == "LEARNING":
            if self.frame_count >= LEARNING_FRAMES:
                self.state = "IDLE"
                print(f"[MOTION GATE] Background learned. Now monitoring for motion...")
            return
        
        # IDLE STATE: Waiting for motion
        if self.state == "IDLE":
            if has_motion:
                self.state = "DETECTING"
                self.motion_frame_count = 1
                print(f"[MOTION GATE] Motion detected! Confirming... (1/{FRAMES_TO_CONFIRM_TRAIN})")
            return
        
        # DETECTING STATE: Confirming train presence
        if self.state == "DETECTING":
            if has_motion:
                self.motion_frame_count += 1
                if self.motion_frame_count % 5 == 0:  # Log every 5 frames
                    print(f"[MOTION GATE] Confirming motion... ({self.motion_frame_count}/{FRAMES_TO_CONFIRM_TRAIN}) - {motion_percentage:.1f}%")
                
                # GATE OPENS: Train confirmed
                if self.motion_frame_count >= FRAMES_TO_CONFIRM_TRAIN:
                    self.state = "ACTIVE"
                    self.no_motion_frame_count = 0
                    print(f"[MOTION GATE] ✓✓✓ GATE OPENED ✓✓✓ Train confirmed! Capturing frames...")
            else:
                # Lost motion, go back to IDLE
                print(f"[MOTION GATE] Motion lost. Returning to IDLE.")
                self.state = "IDLE"
                self.motion_frame_count = 0
            return
        
        # ACTIVE STATE: Capturing frames
        if self.state == "ACTIVE":
            if has_motion:
                self.no_motion_frame_count = 0
            else:
                self.no_motion_frame_count += 1
                if self.no_motion_frame_count % 15 == 0:  # Log every 15 frames
                    print(f"[MOTION GATE] No motion for {self.no_motion_frame_count}/{FRAMES_NO_MOTION_TO_STOP} frames...")
            
            # GATE CLOSES: Train passed
            if self.no_motion_frame_count >= FRAMES_NO_MOTION_TO_STOP:
                self.state = "IDLE"
                print(f"[MOTION GATE] ✗✗✗ GATE CLOSED ✗✗✗ Train passed. Returning to IDLE. ({self.captured_frames} frames captured)")
                self.motion_frame_count = 0
                self.no_motion_frame_count = 0
    
    def process_active_frame(self, frame):
        """
        Process frame when in ACTIVE state.
        This is where you integrate your MIMO deblurring model.
        
        Args:
            frame: BGR image to process
        """
        # Save original frame
        if SAVE_FRAMES:
            self.captured_frames += 1
            timestamp = datetime.now().strftime("%H%M%S_%f")
            frame_path = self.frames_folder / f"frame_{self.captured_frames:06d}_{timestamp}.jpg"
            cv2.imwrite(str(frame_path), frame)
        
        # ==========================================
        # TODO: INTEGRATE MIMO MODEL HERE
        # ==========================================
        # Example integration:
        #
        # 1. Preprocess frame for MIMO model
        #    frame_tensor = preprocess_for_mimo(frame)
        #
        # 2. Run deblurring
        #    deblurred_tensor = mimo_model(frame_tensor)
        #
        # 3. Post-process result
        #    deblurred_frame = postprocess_mimo_output(deblurred_tensor)
        #
        # 4. Run OCR on deblurred frame
        #    wagon_number = ocr_reader.readtext(deblurred_frame)
        #
        # 5. Save results
        #    cv2.imwrite(f"deblurred_{self.captured_frames}.jpg", deblurred_frame)
        # ==========================================
        
        return frame  # Return processed frame for display
    
    def draw_status(self, frame, motion_percentage):
        """Draw status overlay on frame."""
        h, w = frame.shape[:2]
        
        # Semi-transparent overlay
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, 10), (400, 150), (0, 0, 0), -1)
        frame = cv2.addWeighted(frame, 0.7, overlay, 0.3, 0)
        
        # State color coding
        state_colors = {
            "LEARNING": (0, 165, 255),    # Orange
            "IDLE": (128, 128, 128),       # Gray
            "DETECTING": (0, 255, 255),    # Yellow
            "ACTIVE": (0, 255, 0)          # Green
        }
        color = state_colors.get(self.state, (255, 255, 255))
        
        # Draw status text
        cv2.putText(frame, f"STATE: {self.state}", (20, 40), 
                    cv2.FONT_HERSHEY_BOLD, 0.8, color, 2)
        cv2.putText(frame, f"Motion: {motion_percentage:.1f}%", (20, 70),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        cv2.putText(frame, f"Frame: {self.frame_count}", (20, 95),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        if self.state == "ACTIVE":
            cv2.putText(frame, f"Captured: {self.captured_frames}", (20, 120),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)
        
        return frame


# =====================================================
# MAIN FUNCTION
# =====================================================

def main():
    """Main loop: Read from DroidCam, detect motion, capture frames."""
    
    print(f"\n[CAMERA] Connecting to DroidCam: {DROIDCAM_URL}")
    
    # Open video stream
    cap = cv2.VideoCapture(DROIDCAM_URL)
    
    if not cap.isOpened():
        print(f"[ERROR] Failed to connect to {DROIDCAM_URL}")
        print("\nTroubleshooting:")
        print("1. Check DroidCam is running on your phone")
        print("2. Verify the IP address is correct")
        print("3. Make sure phone and computer are on same WiFi")
        print("4. Try accessing the URL in a web browser first")
        return
    
    print("[CAMERA] ✓ Connected successfully!")
    
    # Initialize motion gate
    gate = MotionGate()
    
    print("\n[MOTION GATE] Starting monitoring...")
    print("Press 'q' to quit, 'r' to reset background model")
    print()
    
    try:
        while True:
            # Read frame from camera
            ret, frame = cap.read()
            
            if not ret:
                print("[ERROR] Failed to read frame from camera")
                time.sleep(0.1)
                continue
            
            gate.frame_count += 1
            
            # Detect motion
            has_motion, motion_percentage, fg_mask = gate.detect_motion(frame)
            
            # Update state machine
            gate.update_state(has_motion, motion_percentage)
            
            # Process frame if in ACTIVE state
            if gate.state == "ACTIVE":
                frame = gate.process_active_frame(frame)
            
            # Display preview
            if SHOW_PREVIEW:
                # Draw status overlay
                display_frame = gate.draw_status(frame.copy(), motion_percentage)
                cv2.imshow("Motion Gate - Railway Inspection", display_frame)
                
                # Show motion mask
                if SHOW_MOTION_MASK:
                    fg_mask_colored = cv2.cvtColor(fg_mask, cv2.COLOR_GRAY2BGR)
                    cv2.imshow("Motion Detection Mask", fg_mask_colored)
            
            # Handle keyboard input
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                print("\n[MOTION GATE] Quit requested by user")
                break
            elif key == ord('r'):
                print("\n[MOTION GATE] Resetting background model...")
                gate.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
                    history=BG_HISTORY,
                    varThreshold=BG_VAR_THRESHOLD,
                    detectShadows=True
                )
                gate.state = "LEARNING"
                gate.frame_count = 0
                print("[MOTION GATE] Reset complete. Learning background...")
            
            # Small delay
            time.sleep(0.01)
    
    except KeyboardInterrupt:
        print("\n[MOTION GATE] Interrupted by user (Ctrl+C)")
    
    finally:
        # Cleanup
        print("\n[MOTION GATE] Shutting down...")
        cap.release()
        cv2.destroyAllWindows()
        
        print(f"[MOTION GATE] Session complete. Total frames captured: {gate.captured_frames}")
        if SAVE_FRAMES:
            print(f"[MOTION GATE] Frames saved to: {gate.frames_folder}")
        print("=" * 60)


# =====================================================
# ENTRY POINT
# =====================================================

if __name__ == "__main__":
    main()
