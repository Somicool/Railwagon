"""
SIMPLE Live DroidCam Processor with Terminal Control
=====================================================

Simplified version without threading - beginner friendly!

CONTROLS:
- Type 'start' to begin
- Press 'q' in video window to stop

Features:
- Captures 1 frame per second
- Saves ALL captured frames
- Deblurs frames and saves to single folder

Author: Railway Wagon Inspection System
Date: 2025-12-23
"""

import cv2
import numpy as np
import torch
import sys
from pathlib import Path
from datetime import datetime
from collections import deque

# Import the deblurring model
from models.mimo_official import create_model

# Import damage detector
try:
    import sys
    from pathlib import Path
    # Add railway_dashboard/backend to path for damage detector
    current_file = Path(__file__).resolve()
    backend_path = current_file.parent / 'railway_dashboard' / 'backend'
    print(f"[DEBUG] Looking for damage_detector at: {backend_path}")
    print(f"[DEBUG] Path exists: {backend_path.exists()}")
    if backend_path.exists():
        sys.path.insert(0, str(backend_path))
        print(f"[DEBUG] Added to sys.path: {backend_path}")
    from damage_detector import WagonDamageDetector
    DAMAGE_DETECTION_AVAILABLE = True
    print("[DEBUG] WagonDamageDetector imported successfully")
except ImportError as e:
    print(f"[WARNING] WagonDamageDetector not available: {e}")
    import traceback
    traceback.print_exc()
    DAMAGE_DETECTION_AVAILABLE = False
except Exception as e:
    print(f"[ERROR] Unexpected error importing damage detector: {e}")
    import traceback
    traceback.print_exc()
    DAMAGE_DETECTION_AVAILABLE = False

# Import DroidCam configuration
try:
    from droidcam_config import DROIDCAM_URL, CAMERA_INDICES_TO_TRY, MIN_DROIDCAM_WIDTH, MIN_DROIDCAM_HEIGHT
except ImportError:
    # Fallback if config file not found
    DROIDCAM_URL = "http://192.168.1.8:4747/video"
    CAMERA_INDICES_TO_TRY = [1, 2, 3]
    MIN_DROIDCAM_WIDTH = 640
    MIN_DROIDCAM_HEIGHT = 480


class SimpleLiveProcessor:
    """Simple live video processor - no threading, easy to understand."""
    
    def __init__(self, model_path, output_dir='live_simple_output', 
                 buffer_size=1, save_interval=1, device='cuda'):
        """
        Initialize processor.
        
        Args:
            model_path: Path to model weights
            output_dir: Where to save results
            buffer_size: Frames to buffer (1 = no temporal fusion, better for motion)
            save_interval: Save every N frames (1 = save all)
            device: 'cuda' or 'cpu'
        """
        self.device = device
        self.buffer_size = buffer_size
        self.save_interval = save_interval
        
        # Frame tracking
        self.frame_count = 0
        self.saved_count = 0
        
        # Setup output directories - SINGLE FOLDER FOR ALL DEBLURRED FRAMES + DAMAGE DETECTIONS
        self.output_dir = Path(output_dir)
        self.dirs = {
            'deblurred': self.output_dir / 'deblurred_frames',
            'damage_detections': self.output_dir / 'damage_detections'
        }
        for dir_path in self.dirs.values():
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Frame buffer for temporal fusion
        self.frame_buffer = deque(maxlen=buffer_size)
        
        # Load damage detector
        self.damage_detector = None
        self.damage_detections = []
        print(f"\n[DAMAGE DETECTION] DAMAGE_DETECTION_AVAILABLE = {DAMAGE_DETECTION_AVAILABLE}")
        if DAMAGE_DETECTION_AVAILABLE:
            try:
                print("[DAMAGE DETECTION] Loading Wagon Damage Detector...")
                # Use VERY LOW train coverage threshold for live video
                # Set to 0.01 (1%) to allow detection on nearly all frames
                # This ensures damage detection runs even with partial train views
                self.damage_detector = WagonDamageDetector(
                    device=device,
                    min_train_coverage=0.01  # 1% - nearly always runs
                )
                print("[DAMAGE DETECTION] ✓ Damage Detector loaded successfully")
                print("[DAMAGE DETECTION]   - Min train coverage: 1% (permissive mode)")
                print("[DAMAGE DETECTION]   - Will run on nearly all frames")
            except Exception as e:
                print(f"[DAMAGE DETECTION] ✗ Could not load Damage Detector: {e}")
                import traceback
                traceback.print_exc()
        else:
            print("[DAMAGE DETECTION] Skipping - import failed earlier")
        
        # Load deblurring model
        print("Loading deblurring model...")
        self.model = create_model()
        checkpoint = torch.load(model_path, map_location=device)
        
        # Extract model weights from checkpoint
        if 'model_state_dict' in checkpoint:
            state_dict = checkpoint['model_state_dict']
        else:
            state_dict = checkpoint
        
        self.model.load_state_dict(state_dict, strict=False)
        self.model.to(device)
        self.model.eval()
        print("✓ Model loaded")
    
    def _deblur_frame(self, frame):
        """Deblur a single frame."""
        with torch.no_grad():
            # Prepare input
            h, w = frame.shape[:2]
            img_tensor = torch.from_numpy(frame).permute(2, 0, 1).unsqueeze(0).float() / 255.0
            img_tensor = img_tensor.to(self.device)
            
            # Process
            outputs = self.model(img_tensor)
            
            # Get output
            if isinstance(outputs, (list, tuple)):
                output = outputs[-1]
            else:
                output = outputs
            
            # Convert back
            output = torch.clamp(output, 0, 1)
            output = (output.squeeze().permute(1, 2, 0).cpu().numpy() * 255).astype(np.uint8)
            
            # Ensure correct size
            if output.shape[:2] != (h, w):
                output = cv2.resize(output, (w, h))
            
            return output
    
    def _temporal_fusion(self):
        """Apply temporal fusion on buffered frames."""
        if len(self.frame_buffer) == 0:
            return None
        
        # Simple median fusion
        stacked = np.stack(list(self.frame_buffer), axis=0)
        fused = np.median(stacked, axis=0).astype(np.uint8)
        
        return fused
    
    def _enhance_text(self, frame):
        """Enhance text regions for better visibility."""
        # Convert to LAB
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        # CLAHE on L channel
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        l = clahe.apply(l)
        
        # Merge back
        enhanced = cv2.merge([l, a, b])
        enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
        
        # Sharpening
        kernel = np.array([[-1,-1,-1],
                          [-1, 9,-1],
                          [-1,-1,-1]])
        sharpened = cv2.filter2D(enhanced, -1, kernel)
        
        return sharpened
    
    def _save_frame(self, frame, frame_type='deblurred'):
        """Save frame with timestamp."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        filename = f"frame_{self.saved_count:05d}_{timestamp}.jpg"
        filepath = self.dirs[frame_type] / filename
        
        cv2.imwrite(str(filepath), frame)
        self.saved_count += 1
        
        return filename
    
    def _find_droidcam(self):
        """
        Find DroidCam source.
        Tries:
        1. IP stream
        2. Camera indices 1,2,3 (skips 0 = laptop webcam)
        
        Returns: (cap, source_description) or (None, None)
        """
        print("\nSearching for DroidCam...")
        print("="*60)
        
        # Try IP stream first
        print(f"[Method 1] Trying IP stream: {DROIDCAM_URL}")
        print("  Connecting...", end=" ", flush=True)
        
        cap = cv2.VideoCapture(DROIDCAM_URL)
        
        if cap.isOpened():
            # Verify we can read a frame
            ret, frame = cap.read()
            if ret:
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                print(f"✓ Connected! ({width}x{height})")
                return cap, f"DroidCam IP stream ({DROIDCAM_URL})"
            cap.release()
        
        print("✗ IP stream not available")
        
        # Try camera indices (skip 0 = laptop webcam)
        print("\n[Method 2] Trying camera indices (skipping 0 = laptop webcam)...")
        
        for index in CAMERA_INDICES_TO_TRY:
            print(f"  Trying camera index {index}...", end=" ", flush=True)
            cap = cv2.VideoCapture(index)
            
            if cap.isOpened():
                # Verify we can read a frame
                ret, frame = cap.read()
                if ret:
                    # Check resolution
                    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    
                    # Accept if resolution meets minimum
                    if width >= MIN_DROIDCAM_WIDTH and height >= MIN_DROIDCAM_HEIGHT:
                        print(f"✓ Found! ({width}x{height})")
                        return cap, f"Camera index {index} ({width}x{height})"
                    else:
                        print(f"✗ Too low ({width}x{height})")
                
                cap.release()
            else:
                print("✗ Not available")
        
        # No DroidCam found
        return None, None
    
    def run(self):
        """Main processing loop."""
        print("\n" + "="*60)
        print("STARTING LIVE PROCESSING")
        print("="*60)
        
        # Find DroidCam
        cap, source = self._find_droidcam()
        
        if cap is None:
            print("\n" + "="*60)
            print("ERROR: DroidCam NOT FOUND!")
            print("="*60)
            print("\nTroubleshooting:")
            print("  1. Make sure DroidCam app is running on phone")
            print("  2. Check DroidCam Client is connected on PC")
            print("  3. Update IP address in droidcam_config.py:")
            print("     Edit: droidcam_config.py")
            print("     Change DROIDCAM_IP to your phone's IP")
            print("     (IP shown in DroidCam app)")
            print("\n  4. Or run DroidCam Client to create virtual webcam")
            print("\n  5. Run comprehensive test:")
            print("     python test_droidcam.py")
            print("="*60)
            return
        
        print(f"\n✓ Using: {source}")
        print(f"✓ Capturing at native camera FPS")
        print(f"✓ Saving: Every frame")
        print(f"✓ Output folder: {self.dirs['deblurred']}")
        print("\nPress 'q' in video window to stop")
        print("="*60)
        
        # Main processing loop
        try:
            while True:
                # Read frame
                ret, frame = cap.read()
                
                if not ret:
                    print("Warning: Failed to read frame")
                    continue
                
                self.frame_count += 1
                
                # Step 1: Deblur (main processing)
                print(f"Frame {self.frame_count}...", end=" ", flush=True)
                deblurred = self._deblur_frame(frame)
                
                # Step 2: Text enhancement (CLAHE + sharpen)
                enhanced = self._enhance_text(deblurred)
                
                # Step 3: Damage detection
                damage_result = None
                if self.damage_detector:
                    try:
                        damage_result = self.damage_detector.detect_damage(deblurred)
                        train_cov = damage_result.get('train_coverage', 0) * 100
                        has_damage = damage_result.get('has_damage', False)
                        
                        # Show status
                        if has_damage:
                            print(f"\n>>> DAMAGE! Type: {damage_result['damage_type']}, Conf: {damage_result['confidence']*100:.0f}%, Train: {train_cov:.1f}% <<<", end=" ")
                            # Save damage annotated image
                            damage_img = damage_result['annotated_image']
                            damage_filename = f"damage_{self.frame_count:05d}.jpg"
                            damage_path = self.dirs['damage_detections'] / damage_filename
                            cv2.imwrite(str(damage_path), damage_img)
                            
                            # Track damage
                            self.damage_detections.append({
                                'frame': self.frame_count,
                                'damage_type': damage_result['damage_type'],
                                'confidence': damage_result['confidence']
                            })
                            print(f"⚠ DAMAGE: {damage_result['damage_type']} ({damage_result['confidence']*100:.0f}%)", end=" ")
                    except Exception as e:
                        print(f"Damage detection error: {e}", end=" ")
                
                # Step 4: Save frame
                if self.frame_count % self.save_interval == 0:
                    filename = self._save_frame(enhanced, 'deblurred')
                    print(f"Saved: {filename}")
                else:
                    print("Done")
                
                # Display
                cv2.imshow('Live Processing', enhanced)
                
                # Check for 'q' key
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    print("\n['q' pressed - stopping]")
                    break
        
        except KeyboardInterrupt:
            print("\n[Interrupted]")
        
        finally:
            # Cleanup
            cap.release()
            cv2.destroyAllWindows()
            
            print("\n" + "="*60)
            print("PROCESSING COMPLETE")
            print("="*60)
            print(f"Total frames processed: {self.frame_count}")
            print(f"Total frames saved: {self.saved_count}")
            if self.damage_detector:
                print(f"Damage detections: {len(self.damage_detections)}")
                if self.damage_detections:
                    damage_types = {}
                    for d in self.damage_detections:
                        dt = d['damage_type']
                        damage_types[dt] = damage_types.get(dt, 0) + 1
                    print("  Types detected:")
                    for dtype, count in damage_types.items():
                        print(f"    - {dtype}: {count}")
            print(f"Output location: {self.output_dir}")
            print("="*60)


def main():
    """Main entry point with terminal control."""
    print("\n" + "="*60)
    print("SIMPLE LIVE DROIDCAM PROCESSOR")
    print("="*60)
    print("\nFeatures:")
    print("  ✓ Captures at native camera FPS")
    print("  ✓ Saves ALL captured frames (no skipping)")
    print("  ✓ Deblurs each frame independently")
    print("  ✓ Optimized for moving objects")
    print("  ✓ Single output folder: live_simple_output/deblurred_frames/")
    print("\nControls:")
    print("  - Type 'start' to begin")
    print("  - Press 'q' in video window to stop")
    print("="*60)
    
    # Wait for 'start' command
    while True:
        command = input("\nType 'start' to begin: ").strip().lower()
        if command == 'start':
            break
        else:
            print("Invalid command. Type 'start' to begin.")
    
    # Create processor
    processor = SimpleLiveProcessor(
        model_path='weights/gopro_best.pth',
        output_dir='live_simple_output',
        buffer_size=1,        # No temporal fusion (better for moving objects)
        save_interval=1,      # Save every frame
        device='cuda' if torch.cuda.is_available() else 'cpu'
    )
    
    # Run processing
    processor.run()


if __name__ == '__main__':
    main()
