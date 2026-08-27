"""
Test Live Damage Detection with Video File
===========================================

This script processes a video file as if it's live feed
to demonstrate damage detection working.
"""
import cv2
import sys
from pathlib import Path
import numpy as np
import torch
from collections import deque

# Import damage detector
backend_path = Path(__file__).parent / 'railway_dashboard' / 'backend'
sys.path.insert(0, str(backend_path))
from damage_detector import WagonDamageDetector

# Import deblur model
from models.mimo_official import create_model

def process_video_with_damage_detection(video_path, output_dir='test_live_damage_output'):
    """Process video with damage detection enabled."""
    
    print("="*70)
    print("LIVE DAMAGE DETECTION TEST WITH VIDEO")
    print("="*70)
    
    # Create output directories
    output_dir = Path(output_dir)
    deblurred_dir = output_dir / 'deblurred_frames'
    damage_dir = output_dir / 'damage_detections'
    deblurred_dir.mkdir(parents=True, exist_ok=True)
    damage_dir.mkdir(parents=True, exist_ok=True)
    
    # Load damage detector
    print("\nLoading Wagon Damage Detector...")
    detector = WagonDamageDetector(device='cpu', min_train_coverage=0.01)
    print("✓ Damage Detector loaded (1% threshold - permissive mode)")
    
    # Load deblur model
    print("\nLoading deblur model...")
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    model = create_model()
    
    # Try to load weights
    weights_path = Path('weights/gopro_best.pth')
    if weights_path.exists():
        checkpoint = torch.load(str(weights_path), map_location=device)
        if 'model_state_dict' in checkpoint:
            state_dict = checkpoint['model_state_dict']
        else:
            state_dict = checkpoint
        model.load_state_dict(state_dict, strict=False)
        print("✓ Deblur model loaded")
    else:
        print("⚠ No weights found, using untrained model")
    
    model.to(device)
    model.eval()
    
    # Open video
    print(f"\nOpening video: {video_path}")
    cap = cv2.VideoCapture(str(video_path))
    
    if not cap.isOpened():
        print(f"✗ Could not open video: {video_path}")
        return
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"✓ Video opened: {total_frames} frames @ {fps} fps")
    
    print("\n" + "="*70)
    print("PROCESSING (Press Ctrl+C to stop)")
    print("="*70)
    
    frame_count = 0
    damage_count = 0
    damage_detections = []
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_count += 1
            
            # Process every 10th frame for speed
            if frame_count % 10 != 0:
                continue
            
            print(f"\nFrame {frame_count}/{total_frames}...", end=" ")
            
            # Deblur frame
            with torch.no_grad():
                img_tensor = torch.from_numpy(frame).permute(2, 0, 1).unsqueeze(0).float() / 255.0
                img_tensor = img_tensor.to(device)
                output = model(img_tensor)
                if isinstance(output, (list, tuple)):
                    output = output[-1]
                deblurred = (output.squeeze(0).permute(1, 2, 0).cpu().numpy() * 255).astype(np.uint8)
            
            # Run damage detection
            result = detector.detect_damage(deblurred)
            
            train_cov = result.get('train_coverage', 0) * 100
            has_damage = result.get('has_damage', False)
            
            if has_damage:
                damage_count += 1
                print(f"\n>>> DAMAGE DETECTED! <<<")
                print(f"    Type: {result['damage_type']}")
                print(f"    Confidence: {result['confidence']*100:.1f}%")
                print(f"    Train Coverage: {train_cov:.1f}%")
                
                # Save damage image
                damage_img = result['annotated_image']
                damage_path = damage_dir / f'damage_{frame_count:05d}.jpg'
                cv2.imwrite(str(damage_path), damage_img)
                print(f"    ✓ Saved: {damage_path.name}")
                
                damage_detections.append({
                    'frame': frame_count,
                    'type': result['damage_type'],
                    'confidence': result['confidence']
                })
            else:
                print(f"OK (Train: {train_cov:.1f}%)")
            
            # Save deblurred frame periodically
            if frame_count % 50 == 0:
                deblur_path = deblurred_dir / f'frame_{frame_count:05d}.jpg'
                cv2.imwrite(str(deblur_path), deblurred)
    
    except KeyboardInterrupt:
        print("\n\n[Interrupted by user]")
    
    finally:
        cap.release()
        
        print("\n" + "="*70)
        print("PROCESSING COMPLETE")
        print("="*70)
        print(f"Frames processed: {frame_count}")
        print(f"Damage detections: {damage_count}")
        if damage_detections:
            print("\nDamage Summary:")
            for d in damage_detections:
                print(f"  Frame {d['frame']}: {d['type']} ({d['confidence']*100:.0f}%)")
        print(f"\nOutput saved to: {output_dir}")
        print(f"  - Deblurred frames: {deblurred_dir}")
        print(f"  - Damage images: {damage_dir}")
        print("="*70)


if __name__ == '__main__':
    # Try to find a video file
    video_paths = [
        Path('test_video.mp4'),
        Path('railway_video.mp4'),
        Path('wagon_video.mp4'),
    ]
    
    # Check for videos in sessions folder
    sessions = Path('sessions')
    if sessions.exists():
        video_files = list(sessions.glob('**/*.mp4')) + list(sessions.glob('**/*.avi'))
        if video_files:
            video_paths = video_files[:1] + video_paths
    
    # Find first available video
    video_path = None
    for vp in video_paths:
        if vp.exists():
            video_path = vp
            break
    
    if video_path:
        process_video_with_damage_detection(video_path)
    else:
        print("="*70)
        print("NO VIDEO FILE FOUND")
        print("="*70)
        print("\nPlease provide a video file:")
        print("  python test_video_damage.py path/to/your/video.mp4")
        print("\nOr place a video in one of these locations:")
        for vp in video_paths:
            print(f"  - {vp}")
        print("="*70)
        
        # If video path provided as argument
        if len(sys.argv) > 1:
            video_path = Path(sys.argv[1])
            if video_path.exists():
                process_video_with_damage_detection(video_path)
            else:
                print(f"\n✗ Video not found: {video_path}")
