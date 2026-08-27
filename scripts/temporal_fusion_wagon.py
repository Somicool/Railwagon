"""
Temporal Fusion Pipeline for Wagon Number Detection
====================================================

Multi-frame fusion to recover text from motion-blurred sequences.

WHY TEMPORAL FUSION WORKS:
--------------------------
Single-frame deblurring cannot recover text strokes that are completely
destroyed by directional motion blur. However, across consecutive frames:

1. Blur direction and phase vary as the train moves
2. Missing stroke information in one frame may exist in another
3. Different frames capture different phases of text edge transitions
4. Temporal fusion aggregates complementary information

This is NOT super-resolution or hallucination - it's INFORMATION RECOVERY
from multiple observations of the same physical text.

LIMITATIONS:
------------
- Cannot recover information missing in ALL frames
- Requires reasonable alignment (not extreme blur)
- May fail on very fast motion or poor lighting in all frames
- Does NOT invent digits - only recovers existing information
"""

import os
import cv2
import numpy as np
import torch
from models.mimo_official import MIMOUNetPlus
from pathlib import Path


class TemporalFusionPipeline:
    """Multi-frame temporal fusion for wagon number detection"""
    
    def __init__(self, weights_path='weights/gopro_best.pth'):
        """Initialize pipeline with deblurring model"""
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        print(f"Device: {self.device}")
        
        # Load deblurring model
        print(f"Loading model: {weights_path}")
        self.model = MIMOUNetPlus().to(self.device)
        checkpoint = torch.load(weights_path, map_location=self.device, weights_only=False)
        
        if 'model_state_dict' in checkpoint:
            self.model.load_state_dict(checkpoint['model_state_dict'])
        else:
            self.model.load_state_dict(checkpoint)
        
        self.model.eval()
        print("✓ Model loaded\n")
    
    def deblur_frame(self, image):
        """Apply deblurring to single frame"""
        h, w = image.shape[:2]
        new_h = ((h + 7) // 8) * 8
        new_w = ((w + 7) // 8) * 8
        
        padded = cv2.copyMakeBorder(image, 0, new_h - h, 0, new_w - w, 
                                    cv2.BORDER_REFLECT)
        
        img_tensor = torch.from_numpy(padded).float().permute(2, 0, 1).unsqueeze(0) / 255.0
        img_tensor = img_tensor.to(self.device)
        
        with torch.no_grad():
            outputs = self.model(img_tensor)
            output = outputs[-1] if isinstance(outputs, (list, tuple)) else outputs
        
        output_img = output.squeeze(0).permute(1, 2, 0).cpu().numpy()
        output_img = np.clip(output_img * 255.0, 0, 255).astype(np.uint8)
        output_img = output_img[:h, :w]
        
        return output_img
    
    def extract_wagon_band(self, image, band_start=0.40, band_end=0.60):
        """Extract wagon number search band (40-60% height)"""
        h, w = image.shape[:2]
        y1 = int(h * band_start)
        y2 = int(h * band_end)
        
        band = image[y1:y2, :]
        return band, (y1, y2)
    
    def align_bands(self, bands):
        """
        Align bands using phase correlation (assumes horizontal motion)
        
        Phase correlation is fast and robust for translation estimation.
        Returns aligned bands and shift information.
        """
        # First, resize all bands to the same size (use first band as reference)
        reference = bands[0]
        ref_h, ref_w = reference.shape[:2]
        
        # Resize all bands to match reference size
        resized_bands = [reference]
        for band in bands[1:]:
            if band.shape[:2] != (ref_h, ref_w):
                resized = cv2.resize(band, (ref_w, ref_h), interpolation=cv2.INTER_LINEAR)
                resized_bands.append(resized)
            else:
                resized_bands.append(band)
        
        aligned_bands = [reference]
        shifts = [(0, 0)]
        
        # Convert reference to grayscale for alignment
        ref_gray = cv2.cvtColor(reference, cv2.COLOR_BGR2GRAY)
        
        for i, band in enumerate(resized_bands[1:], 1):
            band_gray = cv2.cvtColor(band, cv2.COLOR_BGR2GRAY)
            
            # Phase correlation for shift estimation
            shift, response = cv2.phaseCorrelate(
                np.float32(ref_gray), 
                np.float32(band_gray)
            )
            
            dx, dy = int(shift[0]), int(shift[1])
            shifts.append((dx, dy))
            
            # Apply translation (primarily horizontal)
            M = np.float32([[1, 0, -dx], [0, 1, -dy]])
            h, w = band.shape[:2]
            aligned = cv2.warpAffine(band, M, (w, h), 
                                     flags=cv2.INTER_LINEAR,
                                     borderMode=cv2.BORDER_REFLECT)
            
            aligned_bands.append(aligned)
            
            print(f"  Frame {i+1}: shift=({dx:+4d}, {dy:+3d}) px, confidence={response:.3f}")
        
        return aligned_bands, shifts
    
    def fusion_median(self, bands):
        """
        OPTION A: Median fusion (ROBUST baseline)
        
        Takes pixel-wise median across frames.
        - Robust to outliers (e.g., compression artifacts)
        - Preserves edges well
        - Good for moderate blur
        """
        stack = np.stack(bands, axis=0)
        fused = np.median(stack, axis=0).astype(np.uint8)
        return fused
    
    def fusion_max_gradient(self, bands):
        """
        OPTION B: Max-gradient fusion (EDGE-PRESERVING)
        
        For each pixel, select the value from the frame with
        strongest local gradient (sharpest edge).
        
        - Excellent for recovering text edges
        - Preserves sharp transitions
        - May amplify noise slightly
        """
        # Compute gradients for each band
        gradients = []
        for band in bands:
            gray = cv2.cvtColor(band, cv2.COLOR_BGR2GRAY)
            
            # Sobel gradients
            gx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
            gy = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
            grad_mag = np.sqrt(gx**2 + gy**2)
            
            gradients.append(grad_mag)
        
        # Stack gradients and find max
        grad_stack = np.stack(gradients, axis=0)
        max_indices = np.argmax(grad_stack, axis=0)
        
        # Build fused image by selecting from frame with max gradient
        h, w, c = bands[0].shape
        fused = np.zeros((h, w, c), dtype=np.uint8)
        
        for i in range(len(bands)):
            mask = (max_indices == i)
            for ch in range(c):
                fused[:, :, ch][mask] = bands[i][:, :, ch][mask]
        
        return fused
    
    def fusion_weighted_sharpness(self, bands):
        """
        OPTION C: Weighted average by local sharpness
        
        Weight each pixel by local variance (sharpness measure).
        Sharper regions contribute more to the final result.
        
        - Smooth transitions between frames
        - Good for varying blur levels
        - More computationally expensive
        """
        weights = []
        window_size = 15  # Local window for variance
        
        for band in bands:
            gray = cv2.cvtColor(band, cv2.COLOR_BGR2GRAY).astype(np.float32)
            
            # Local variance as sharpness measure
            mean = cv2.boxFilter(gray, -1, (window_size, window_size))
            sqr_mean = cv2.boxFilter(gray**2, -1, (window_size, window_size))
            variance = sqr_mean - mean**2
            variance = np.maximum(variance, 0)  # Numerical stability
            
            weights.append(variance)
        
        # Normalize weights
        weight_stack = np.stack(weights, axis=0)
        weight_sum = np.sum(weight_stack, axis=0, keepdims=True)
        weight_sum = np.maximum(weight_sum, 1e-6)  # Avoid division by zero
        normalized_weights = weight_stack / weight_sum
        
        # Weighted fusion
        fused = np.zeros_like(bands[0], dtype=np.float32)
        for i, band in enumerate(bands):
            weight = normalized_weights[i]
            for ch in range(3):
                fused[:, :, ch] += band[:, :, ch] * weight
        
        fused = np.clip(fused, 0, 255).astype(np.uint8)
        return fused
    
    def post_enhance(self, image):
        """
        Post-fusion text enhancement
        
        - Apply CLAHE on L channel (LAB color space)
        - Mild sharpening
        - Preserve color for visualization
        """
        # Convert to LAB
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        # CLAHE on L channel (mild settings)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l_enhanced = clahe.apply(l)
        
        # Merge back
        lab_enhanced = cv2.merge([l_enhanced, a, b])
        enhanced = cv2.cvtColor(lab_enhanced, cv2.COLOR_LAB2BGR)
        
        # Mild sharpening (unsharp mask)
        blurred = cv2.GaussianBlur(enhanced, (0, 0), 1.5)
        sharpened = cv2.addWeighted(enhanced, 1.5, blurred, -0.5, 0)
        sharpened = np.clip(sharpened, 0, 255).astype(np.uint8)
        
        return sharpened
    
    def process_sequence(self, frame_paths, output_dir='temporal_fusion_results',
                        fusion_method='median', run_ocr=True, ocr_confidence=0.4):
        """
        Process complete temporal fusion pipeline
        
        Args:
            frame_paths: List of paths to consecutive frames
            output_dir: Output directory for results
            fusion_method: 'median', 'max_gradient', or 'weighted'
            run_ocr: Whether to run OCR on deblurred images
            ocr_confidence: OCR confidence threshold
        """
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(f"{output_dir}/step1_deblurred", exist_ok=True)
        os.makedirs(f"{output_dir}/step2_bands", exist_ok=True)
        os.makedirs(f"{output_dir}/step3_aligned", exist_ok=True)
        
        print("=" * 70)
        print("TEMPORAL FUSION PIPELINE - WAGON NUMBER DETECTION")
        print("=" * 70)
        print(f"Input frames: {len(frame_paths)}")
        print(f"Fusion method: {fusion_method.upper()}")
        print(f"Output: {output_dir}/\n")
        
        # STEP 1: Per-frame processing
        print("STEP 1: Per-frame Enhancement & Band Extraction")
        print("-" * 70)
        
        bands = []
        for i, frame_path in enumerate(frame_paths, 1):
            print(f"Frame {i}/{len(frame_paths)}: {Path(frame_path).name}")
            
            # Load frame
            with open(frame_path, 'rb') as f:
                image_data = np.frombuffer(f.read(), dtype=np.uint8)
            frame = cv2.imdecode(image_data, cv2.IMREAD_COLOR)
            
            # Deblur
            print(f"  Deblurring...")
            deblurred = self.deblur_frame(frame)
            cv2.imwrite(f"{output_dir}/step1_deblurred/frame_{i}_deblurred.png", deblurred)
            
            # Extract band
            band, (y1, y2) = self.extract_wagon_band(deblurred)
            print(f"  Band extracted: y={y1}..{y2} (height={band.shape[0]} px)")
            cv2.imwrite(f"{output_dir}/step2_bands/frame_{i}_band.png", band)
            
            bands.append(band)
            print()
        
        # STEP 2: Temporal alignment
        print("\nSTEP 2: Temporal Alignment (Phase Correlation)")
        print("-" * 70)
        aligned_bands, shifts = self.align_bands(bands)
        
        for i, aligned in enumerate(aligned_bands, 1):
            cv2.imwrite(f"{output_dir}/step3_aligned/frame_{i}_aligned.png", aligned)
        print()
        
        # STEP 3: Temporal fusion
        print("\nSTEP 3: Temporal Fusion")
        print("-" * 70)
        
        if fusion_method == 'median':
            print("Method: MEDIAN FUSION (robust baseline)")
            fused = self.fusion_median(aligned_bands)
        elif fusion_method == 'max_gradient':
            print("Method: MAX-GRADIENT FUSION (edge-preserving)")
            fused = self.fusion_max_gradient(aligned_bands)
        elif fusion_method == 'weighted':
            print("Method: WEIGHTED SHARPNESS FUSION")
            fused = self.fusion_weighted_sharpness(aligned_bands)
        else:
            raise ValueError(f"Unknown fusion method: {fusion_method}")
        
        cv2.imwrite(f"{output_dir}/fused_band.png", fused)
        print("✓ Fusion complete\n")
        
        # STEP 4: Post-enhancement
        print("\nSTEP 4: Post-Fusion Text Enhancement")
        print("-" * 70)
        enhanced = self.post_enhance(fused)
        cv2.imwrite(f"{output_dir}/enhanced_fused_band.png", enhanced)
        print("✓ Enhanced with CLAHE + sharpening")
        
        # OCR-ready grayscale
        ocr_input = cv2.cvtColor(enhanced, cv2.COLOR_BGR2GRAY)
        cv2.imwrite(f"{output_dir}/final_ocr_input.png", ocr_input)
        print("✓ Grayscale OCR input ready\n")
        
        # Create comparison visualization
        self.create_comparison(bands, aligned_bands, fused, enhanced, output_dir)
        
        print("=" * 70)
        print("PIPELINE COMPLETE")
        print("=" * 70)
        print(f"\nResults saved in: {output_dir}/")
        print("\nOutput files:")
        print("  - fused_band.png           : Temporally fused band")
        print("  - enhanced_fused_band.png  : Post-enhanced result")
        print("  - final_ocr_input.png      : Grayscale for OCR")
        print("  - comparison_grid.png      : Visual comparison")
        
        # OPTIONAL: Run OCR on all deblurred frames
        if run_ocr:
            print("\n" + "=" * 70)
            print("RUNNING OCR ON DEBLURRED FRAMES")
            print("=" * 70)
            
            try:
                from run_ocr_wagon import WagonNumberOCR
                
                # Initialize OCR
                ocr_system = WagonNumberOCR(confidence_threshold=ocr_confidence)
                
                # Run OCR on each deblurred frame
                ocr_results = []
                deblurred_dir = f"{output_dir}/step1_deblurred"
                
                for i in range(1, len(frame_paths) + 1):
                    deblurred_path = f"{deblurred_dir}/frame_{i}_deblurred.png"
                    
                    if os.path.exists(deblurred_path):
                        print(f"\nFrame {i}:")
                        print("-" * 70)
                        
                        result = ocr_system.extract_wagon_number(
                            deblurred_path, 
                            output_dir=deblurred_dir,
                            save_visualization=True
                        )
                        
                        ocr_results.append({
                            'frame': i,
                            'path': deblurred_path,
                            'wagon_number': result['wagon_number'],
                            'confidence': result['confidence']
                        })
                        
                        # Save individual wagon number image
                        if result['wagon_number'] != 'UNREADABLE':
                            os.rename(
                                f"{deblurred_dir}/detected_wagon_number.png",
                                f"{deblurred_dir}/frame_{i}_wagon_number.png"
                            )
                
                # Also run on final fused output
                print(f"\nFinal Fused Image:")
                print("-" * 70)
                
                final_ocr_path = f"{output_dir}/final_ocr_input.png"
                final_result = ocr_system.extract_wagon_number(
                    final_ocr_path,
                    output_dir=output_dir,
                    save_visualization=True
                )
                
                # Print OCR summary
                print("\n" + "=" * 70)
                print("OCR SUMMARY")
                print("=" * 70)
                
                readable_count = sum(1 for r in ocr_results if r['wagon_number'] != 'UNREADABLE')
                
                print(f"\nPer-frame results:")
                for result in ocr_results:
                    status = "✓" if result['wagon_number'] != 'UNREADABLE' else "✗"
                    print(f"  {status} Frame {result['frame']}: {result['wagon_number']} (conf: {result['confidence']:.3f})")
                
                print(f"\nFinal fused: {final_result['wagon_number']} (conf: {final_result['confidence']:.3f})")
                print(f"\nReadable frames: {readable_count}/{len(ocr_results)}")
                print("=" * 70)
                
            except ImportError:
                print("\n⚠ OCR module not available. Install: pip install easyocr")
            except Exception as e:
                print(f"\n⚠ OCR error: {e}")
        
        print("\nNext step: Check OCR results in output directory")
        print("=" * 70)
    
    def create_comparison(self, original_bands, aligned_bands, fused, enhanced, output_dir):
        """Create visual comparison grid"""
        # Resize for display
        display_width = 800
        h, w = original_bands[0].shape[:2]
        aspect = h / w
        display_height = int(display_width * aspect)
        
        def resize_with_label(img, label):
            resized = cv2.resize(img, (display_width, display_height))
            labeled = resized.copy()
            cv2.putText(labeled, label, (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                       0.9, (0, 255, 0), 2, cv2.LINE_AA)
            return labeled
        
        # Create grid: original frames, aligned frames, fused, enhanced
        rows = []
        
        # Row 1-2: Original and aligned bands
        for i in range(len(original_bands)):
            orig_labeled = resize_with_label(original_bands[i], f"Original Frame {i+1}")
            aligned_labeled = resize_with_label(aligned_bands[i], f"Aligned Frame {i+1}")
            rows.extend([orig_labeled, aligned_labeled])
        
        # Row final: Fused and enhanced
        fused_labeled = resize_with_label(fused, "FUSED (Temporal)")
        enhanced_labeled = resize_with_label(enhanced, "ENHANCED (Final)")
        rows.extend([fused_labeled, enhanced_labeled])
        
        # Stack all rows
        comparison = np.vstack(rows)
        cv2.imwrite(f"{output_dir}/comparison_grid.png", comparison)


def main():
    """Example usage"""
    import tkinter as tk
    from tkinter import filedialog
    
    # Browse for first frame
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    
    print("Select FIRST frame of the sequence...")
    first_frame = filedialog.askopenfilename(
        title="Select FIRST frame (e.g., frame_1.png)",
        filetypes=[("Image files", "*.png *.jpg *.jpeg"), ("All files", "*.*")]
    )
    
    if not first_frame:
        print("No file selected.")
        return
    
    # Auto-detect sequence
    base_dir = os.path.dirname(first_frame)
    base_name = os.path.basename(first_frame)
    
    # Ask how many frames in sequence
    print(f"\nFirst frame: {base_name}")
    num_frames = int(input("How many frames in sequence (3-5)? "))
    
    # Generate frame paths
    frame_paths = []
    for i in range(1, num_frames + 1):
        # Try common naming patterns
        patterns = [
            os.path.join(base_dir, f"frame_{i}.png"),
            os.path.join(base_dir, f"frame{i}.png"),
            os.path.join(base_dir, base_name.replace("1", str(i))),
        ]
        
        found = False
        for pattern in patterns:
            if os.path.exists(pattern):
                frame_paths.append(pattern)
                found = True
                break
        
        if not found and i == 1:
            frame_paths.append(first_frame)
        elif not found:
            print(f"Warning: Could not find frame {i}")
    
    if len(frame_paths) < 2:
        print("Error: Need at least 2 frames for temporal fusion")
        return
    
    print(f"\nFound {len(frame_paths)} frames")
    
    # Choose fusion method
    print("\nFusion methods:")
    print("  1. Median (robust, recommended)")
    print("  2. Max-gradient (edge-preserving, best for text)")
    print("  3. Weighted sharpness (smooth, slower)")
    
    method_choice = input("Choose method (1-3) [default=2]: ").strip()
    
    methods = {
        '1': 'median',
        '2': 'max_gradient',
        '3': 'weighted',
        '': 'max_gradient'  # default
    }
    fusion_method = methods.get(method_choice, 'max_gradient')
    
    # Run pipeline
    pipeline = TemporalFusionPipeline(weights_path='weights/gopro_best.pth')
    pipeline.process_sequence(frame_paths, 
                            output_dir='temporal_fusion_results',
                            fusion_method=fusion_method)


if __name__ == '__main__':
    main()
