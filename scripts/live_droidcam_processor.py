"""
Live DroidCam Video Processor with Terminal Control
===================================================

Real-time video processing pipeline for railway wagon detection
from DroidCam feed with simple terminal control.

CONTROLS:
- Type 'start' to begin live processing
- Type 'stop' in terminal OR press 'q' in video window to stop

Author: Railway Wagon Inspection System
Date: 2025-12-23
"""

import cv2
import numpy as np
import torch
import threading
import queue
import time
import sys
from pathlib import Path
from datetime import datetime
from collections import deque

# Import the deblurring model
from models.mimo_unet_plus import MIMOUNetPlus

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
    DROIDCAM_URL = "http://192.168.1.100:4747/video"
    CAMERA_INDICES_TO_TRY = [1, 2, 3]
    MIN_DROIDCAM_WIDTH = 640
    MIN_DROIDCAM_HEIGHT = 480


class LiveDroidCamProcessor:
    """Live video processor with terminal control for DroidCam."""
    
    def __init__(self, model_path, output_dir='live_output', 
                 buffer_size=3, save_interval=30, device='cuda'):
        """
        Initialize live processor.
        
        Args:
            model_path (str): Path to deblurring model weights
            output_dir (str): Directory to save processed frames
            buffer_size (int): Number of frames to buffer for temporal fusion
            save_interval (int): Save results every N frames
            device (str): 'cuda' or 'cpu'
        """
        self.device = device if torch.cuda.is_available() else 'cpu'
        self.output_dir = Path(output_dir)
        self.buffer_size = buffer_size
        self.save_interval = save_interval
        
        # Control flags
        self.running = False
        self.stop_requested = False
        
        # Frame buffer for temporal fusion
        self.frame_buffer = deque(maxlen=buffer_size)
        
        # Processing counters
        self.frame_count = 0
        self.saved_count = 0
        
        # Create output directories
        self._setup_output_dirs()
        
        # Load model
        print(f"Loading deblurring model from {model_path}...")
        self.model = self._load_model(model_path)
        print(f"✓ Model loaded successfully on {self.device}")
        
        # Load OCR (optional)
        self._load_ocr()
        
        # Load damage detector (optional)
        self.damage_detector = None
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
        
        # Damage detection tracking
        self.damage_detections = []
        
        print("="*70)
        print("LIVE DROIDCAM PROCESSOR INITIALIZED")
        print("="*70)
        print(f"Device: {self.device}")
        print(f"Buffer size: {buffer_size} frames")
        print(f"Save interval: Every {save_interval} frames")
        print(f"Output directory: {output_dir}")
        print(f"Damage Detection: {'ENABLED' if self.damage_detector else 'DISABLED'}")
        print("="*70)
    
    def _setup_output_dirs(self):
        """Create output directory structure."""
        self.dirs = {
            'raw': self.output_dir / "1_raw_frames",
            'deblurred': self.output_dir / "2_deblurred",
            'enhanced': self.output_dir / "3_enhanced",
            'ocr_results': self.output_dir / "4_ocr_results",
            'damage_detections': self.output_dir / "5_damage_detections"
        }
        
        for dir_path in self.dirs.values():
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def _load_model(self, model_path):
        """Load deblurring model."""
        model = MIMOUNetPlus()
        
        checkpoint = torch.load(model_path, map_location=self.device)
        
        if 'model_state_dict' in checkpoint:
            state_dict = checkpoint['model_state_dict']
        elif 'state_dict' in checkpoint:
            state_dict = checkpoint['state_dict']
        else:
            state_dict = checkpoint
        
        model.load_state_dict(state_dict, strict=False)
        model.to(self.device)
        model.eval()
        
        return model
    
    def _load_ocr(self):
        """Load OCR engine (optional)."""
        self.ocr_reader = None
        try:
            import easyocr
            print("Loading EasyOCR...")
            self.ocr_reader = easyocr.Reader(['en'], gpu=torch.cuda.is_available())
            print("✓ EasyOCR loaded successfully")
        except Exception as e:
            print(f"Note: OCR not available ({e})")
            print("Install easyocr for text detection: pip install easyocr")
    
    def _preprocess_frame(self, frame):
        """Preprocess frame for model input."""
        # Convert BGR to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Normalize to [0, 1]
        frame_norm = frame_rgb.astype(np.float32) / 255.0
        
        # Convert to tensor (H, W, C) -> (C, H, W)
        frame_tensor = torch.from_numpy(frame_norm).permute(2, 0, 1).unsqueeze(0)
        
        return frame_tensor.to(self.device)
    
    def _postprocess_frame(self, tensor):
        """Convert model output back to image."""
        # Remove batch dimension and move to CPU
        output = tensor.squeeze(0).cpu().detach().numpy()
        
        # (C, H, W) -> (H, W, C)
        output = np.transpose(output, (1, 2, 0))
        
        # Clip to [0, 1] and convert to uint8
        output = np.clip(output * 255, 0, 255).astype(np.uint8)
        
        # Convert RGB back to BGR for OpenCV
        output = cv2.cvtColor(output, cv2.COLOR_RGB2BGR)
        
        return output
    
    def _deblur_frame(self, frame):
        """Apply deblurring to single frame."""
        with torch.no_grad():
            input_tensor = self._preprocess_frame(frame)
            output_tensor = self.model(input_tensor)
            deblurred = self._postprocess_frame(output_tensor)
        
        return deblurred
    
    def _temporal_fusion(self):
        """Fuse buffered frames using median."""
        if len(self.frame_buffer) < 2:
            return self.frame_buffer[-1] if self.frame_buffer else None
        
        # Stack frames and compute median
        frames_array = np.array(list(self.frame_buffer))
        fused = np.median(frames_array, axis=0).astype(np.uint8)
        
        return fused
    
    def _enhance_for_text(self, frame):
        """Apply text-specific enhancement (CLAHE + sharpening)."""
        # Convert to LAB color space
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        # Apply CLAHE to L channel
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        l_enhanced = clahe.apply(l)
        
        # Merge back
        enhanced_lab = cv2.merge([l_enhanced, a, b])
        enhanced = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)
        
        # Apply sharpening kernel
        kernel = np.array([[-1, -1, -1],
                          [-1,  9, -1],
                          [-1, -1, -1]])
        sharpened = cv2.filter2D(enhanced, -1, kernel)
        
        return sharpened
    
    def _run_ocr(self, frame):
        """Run OCR on frame (if available)."""
        if self.ocr_reader is None:
            return []
        
        try:
            results = self.ocr_reader.readtext(frame)
            # Filter for wagon number patterns (digits)
            detections = []
            for bbox, text, conf in results:
                # Look for 4+ digit patterns
                if len(text) >= 4 and any(c.isdigit() for c in text):
                    detections.append({
                        'text': text,
                        'confidence': conf,
                        'bbox': bbox
                    })
            return detections
        except Exception as e:
            print(f"OCR error: {e}")
            return []
    
    def _save_frame(self, frame, frame_type='raw'):
        """Save frame to appropriate directory."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        filename = f"{frame_type}_{self.saved_count:05d}_{timestamp}.jpg"
        filepath = self.dirs[frame_type] / filename
        cv2.imwrite(str(filepath), frame)
        return filepath
    
    def _process_frame(self, frame):
        """Process single frame through pipeline."""
        # Deblur the frame
        deblurred = self._deblur_frame(frame)
        
        # Add to buffer for temporal fusion
        self.frame_buffer.append(deblurred)
        
        # Temporal fusion
        fused = self._temporal_fusion()
        
        # Text enhancement
        enhanced = self._enhance_for_text(fused)
        
        return deblurred, fused, enhanced
    
    def _listen_for_stop(self):
        """Listen for 'stop' command in separate thread."""
        while self.running:
            try:
                # Non-blocking input check
                user_input = input()
                if user_input.strip().lower() == 'stop':
                    print("\n[STOP command received]")
                    self.stop_requested = True
                    self.running = False
                    break
            except:
                pass
    
    def _find_droidcam(self):
        """
        Smart DroidCam detection (same as simple version).
        """
        print("Searching for DroidCam...")
        print("\n[Method 1] Trying DroidCam IP stream...")
        print(f"  URL: {DROIDCAM_URL}")
        
        cap = cv2.VideoCapture(DROIDCAM_URL)
        
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                print(f"  ✓ Connected! ({width}x{height})")
                return cap, f"DroidCam IP stream ({DROIDCAM_URL})"
            cap.release()
        
        print("  ✗ IP stream not available")
        
        print("\n[Method 2] Trying camera indices (skipping 0 = laptop webcam)...")
        
        for index in CAMERA_INDICES_TO_TRY:
            print(f"  Trying camera index {index}...")
            cap = cv2.VideoCapture(index)
            
            if cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    
                    if width >= MIN_DROIDCAM_WIDTH and height >= MIN_DROIDCAM_HEIGHT:
                        print(f"  ✓ Found camera at index {index} ({width}x{height})")
                        return cap, f"Camera index {index} ({width}x{height})"
                    else:
                        print(f"  ✗ Resolution too low ({width}x{height})")
                
                cap.release()
            else:
                print(f"  ✗ Index {index} not available")
        
        return None, None
    
    def start(self):
        """Start live processing."""
        print("\n" + "="*70)
        print("STARTING LIVE PROCESSING")
        print("="*70)
        
        # Find DroidCam
        cap, source = self._find_droidcam()
        
        if cap is None:
            print("\n" + "="*70)
            print("ERROR: DroidCam NOT FOUND!")
            print("="*70)
            print("\nTroubleshooting:")
            print("  1. Make sure DroidCam app is running on phone")
            print("  2. Check DroidCam Client is connected on PC")
            print("  3. Update IP address in script if using IP stream:")
            print("     Edit live_droidcam_processor.py line ~150")
            print("     Change: droidcam_ip = '192.168.1.100'")
            print("     To your phone's IP address")
            print("\n  4. Or run DroidCam Client to create virtual webcam")
            print("="*70)
            return
        
        print("\n" + "="*70)
        print(f"✓ CONNECTED TO: {source}")
        print("="*70)
        print("\nCONTROLS:")
        print("  - Type 'stop' in terminal to stop")
        print("  - Press 'q' in video window to stop")
        print("="*70)
        
        # Start thread to listen for 'stop' command
        stop_thread = threading.Thread(target=self._listen_for_stop, daemon=True)
        stop_thread.start()
        
        # Processing loop
        try:
            while self.running:
                ret, frame = cap.read()
                
                if not ret:
                    print("Warning: Failed to read frame")
                    continue
                
                self.frame_count += 1
                
                # Process frame
                deblurred, fused, enhanced = self._process_frame(frame)
                
                # Display live video (optional)
                display_frame = cv2.resize(enhanced, (960, 540))
                cv2.putText(display_frame, f"Frame: {self.frame_count}", 
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                cv2.putText(display_frame, "Press 'q' to stop", 
                           (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                cv2.imshow('Live Processing', display_frame)
                
                # Run damage detection if available
                damage_result = None
                if self.damage_detector:
                    try:
                        damage_result = self.damage_detector.detect_damage(deblurred)
                        
                        # Always show status for debugging
                        train_cov = damage_result.get('train_coverage', 0) * 100
                        has_damage = damage_result.get('has_damage', False)
                        
                        # Show status every frame (for debugging)
                        if has_damage:
                            print(f"\n>>> Frame {self.frame_count}: DAMAGE DETECTED! <<<")
                            print(f"    Type: {damage_result['damage_type']}")
                            print(f"    Confidence: {damage_result['confidence']*100:.1f}%")
                            print(f"    Train Coverage: {train_cov:.1f}%")
                            print(f"    Damage Count: {damage_result['damage_count']}")
                            
                            # Save damage annotated image
                            damage_img = damage_result['annotated_image']
                            damage_path = self.dirs['damage_detections'] / f'damage_{self.frame_count:05d}.jpg'
                            cv2.imwrite(str(damage_path), damage_img)
                            
                            # Track damage detection
                            self.damage_detections.append({
                                'frame': self.frame_count,
                                'damage_type': damage_result['damage_type'],
                                'damage_types': damage_result['damage_types'],
                                'confidence': damage_result['confidence'],
                                'damage_count': damage_result['damage_count']
                            })
                    except Exception as e:
                        print(f"Error in damage detection: {e}")
                
                # Save frames at intervals
                if self.frame_count % self.save_interval == 0:
                    self._save_frame(frame, 'raw')
                    self._save_frame(deblurred, 'deblurred')
                    self._save_frame(enhanced, 'enhanced')
                    self.saved_count += 1
                    
                    # Include damage info in status
                    damage_info = f" | Damages: {len(self.damage_detections)}" if self.damage_detector else ""
                    print(f"[Saved {self.saved_count} sets | Total frames: {self.frame_count}{damage_info}]")
                
                # Check for 'q' key press
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    print("\n['q' key pressed in video window]")
                    self.running = False
                    break
                
                # Check if stop was requested
                if self.stop_requested:
                    break
        
        except KeyboardInterrupt:
            print("\n[Keyboard interrupt received]")
        
        except Exception as e:
            print(f"\nERROR during processing: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            # Clean up
            print("\nCleaning up...")
            cap.release()
            cv2.destroyAllWindows()
            self.running = False
            
            print("\n" + "="*70)
            print("LIVE PROCESSING STOPPED SUCCESSFULLY")
            print("="*70)
            print(f"Total frames processed: {self.frame_count}")
            print(f"Frame sets saved: {self.saved_count}")
            if self.damage_detector:
                print(f"Damage detections: {len(self.damage_detections)}")
                if self.damage_detections:
                    damage_types = {}
                    for d in self.damage_detections:
                        dt = d['damage_type']
                        damage_types[dt] = damage_types.get(dt, 0) + 1
                    print("  Breakdown:")
                    for dtype, count in damage_types.items():
                        print(f"    - {dtype}: {count}")
            print(f"Output directory: {self.output_dir}")
            print("="*70)


def main():
    """Main entry point with terminal control."""
    
    print("\n" + "="*70)
    print("LIVE DROIDCAM PROCESSOR - TERMINAL CONTROL")
    print("="*70)
    print("\nType 'start' to begin live processing")
    print("Type 'stop' or press 'q' in video window to stop")
    print("="*70)
    
    # Wait for 'start' command
    while True:
        user_input = input("\nCommand: ").strip().lower()
        
        if user_input == 'start':
            break
        elif user_input == 'exit' or user_input == 'quit':
            print("Exiting...")
            sys.exit(0)
        else:
            print("Invalid command. Type 'start' to begin or 'exit' to quit.")
    
    # Initialize processor
    try:
        processor = LiveDroidCamProcessor(
            model_path='weights/gopro_best.pth',
            output_dir='live_output',
            buffer_size=3,
            save_interval=30,  # Save every 30 frames
            device='cuda' if torch.cuda.is_available() else 'cpu'
        )
        
        # Start processing
        processor.start()
        
    except FileNotFoundError as e:
        print(f"\nERROR: {e}")
        print("\nMake sure 'weights/gopro_best.pth' exists!")
        print("If you don't have the model weights, train the model first.")
    
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
    
    print("\nProgram ended.")


if __name__ == "__main__":
    main()
