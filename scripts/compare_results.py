"""
Compare blur, sharp (ground truth), and deblurred images side by side
"""

import os
import cv2
import numpy as np
import torch
from models.mimo_unet_plus import MIMOUNetPlus
import argparse


def load_and_process(image_path, device, model=None):
    """Load image and optionally deblur it"""
    img = cv2.imread(image_path)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    if model is not None:
        # Pad image to multiple of 16 for model
        h, w = img_rgb.shape[:2]
        pad_h = (16 - h % 16) % 16
        pad_w = (16 - w % 16) % 16
        
        img_padded = np.pad(img_rgb, ((0, pad_h), (0, pad_w), (0, 0)), mode='reflect')
        
        # Deblur with model
        img_tensor = torch.from_numpy(img_padded).float().permute(2, 0, 1) / 255.0
        img_tensor = img_tensor.unsqueeze(0).to(device)
        
        with torch.no_grad():
            outputs = model(img_tensor)
            deblurred = outputs[0].squeeze(0).permute(1, 2, 0).cpu().numpy()
            deblurred = np.clip(deblurred * 255.0, 0, 255).astype(np.uint8)
            
            # Remove padding
            deblurred = deblurred[:h, :w]
        
        return img_rgb, deblurred
    
    return img_rgb


def create_comparison(blur_path, sharp_path, model, device, output_path):
    """Create side-by-side comparison"""
    # Load images
    blur_img, deblurred_img = load_and_process(blur_path, device, model)
    sharp_img = load_and_process(sharp_path, device, model=None)
    
    # Resize to same height
    h = min(blur_img.shape[0], sharp_img.shape[0], deblurred_img.shape[0])
    w = min(blur_img.shape[1], sharp_img.shape[1], deblurred_img.shape[1])
    
    blur_img = cv2.resize(blur_img, (w, h))
    sharp_img = cv2.resize(sharp_img, (w, h))
    deblurred_img = cv2.resize(deblurred_img, (w, h))
    
    # Add labels
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 1.0
    thickness = 2
    color = (255, 255, 255)
    
    blur_labeled = blur_img.copy()
    sharp_labeled = sharp_img.copy()
    deblurred_labeled = deblurred_img.copy()
    
    cv2.putText(blur_labeled, 'Blur (Input)', (10, 40), font, font_scale, color, thickness)
    cv2.putText(sharp_labeled, 'Sharp (GT)', (10, 40), font, font_scale, color, thickness)
    cv2.putText(deblurred_labeled, 'Deblurred', (10, 40), font, font_scale, color, thickness)
    
    # Calculate PSNR
    mse_deblur = np.mean((deblurred_img.astype(float) - sharp_img.astype(float)) ** 2)
    mse_blur = np.mean((blur_img.astype(float) - sharp_img.astype(float)) ** 2)
    
    if mse_deblur > 0:
        psnr_deblur = 20 * np.log10(255.0 / np.sqrt(mse_deblur))
    else:
        psnr_deblur = float('inf')
    
    if mse_blur > 0:
        psnr_blur = 20 * np.log10(255.0 / np.sqrt(mse_blur))
    else:
        psnr_blur = float('inf')
    
    cv2.putText(deblurred_labeled, f'PSNR: {psnr_deblur:.2f} dB', (10, 80), 
                font, font_scale * 0.7, (0, 255, 0), thickness)
    cv2.putText(blur_labeled, f'PSNR: {psnr_blur:.2f} dB', (10, 80), 
                font, font_scale * 0.7, (255, 0, 0), thickness)
    
    # Concatenate horizontally
    comparison = np.hstack([blur_labeled, deblurred_labeled, sharp_labeled])
    
    # Convert to BGR and save
    comparison_bgr = cv2.cvtColor(comparison, cv2.COLOR_RGB2BGR)
    cv2.imwrite(output_path, comparison_bgr)
    
    return psnr_blur, psnr_deblur


def main():
    parser = argparse.ArgumentParser(description='Compare deblurring results')
    parser.add_argument('--model', type=str, required=True,
                        help='Path to fine-tuned model')
    parser.add_argument('--num_samples', type=int, default=5,
                        help='Number of samples to compare')
    parser.add_argument('--blur_dir', type=str, default='train/train/blur',
                        help='Blur images directory')
    parser.add_argument('--sharp_dir', type=str, default='train/train/sharp',
                        help='Sharp images directory')
    parser.add_argument('--output_dir', type=str, default='comparison_results',
                        help='Output directory')
    
    args = parser.parse_args()
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Device
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Using device: {device}\n")
    
    # Load model
    print(f"Loading model: {args.model}")
    model = MIMOUNetPlus(num_res=8).to(device)
    
    if args.model.endswith('.pkl'):
        model.load_state_dict(torch.load(args.model, map_location=device))
    else:
        checkpoint = torch.load(args.model, map_location=device)
        model.load_state_dict(checkpoint['model_state_dict'])
        if 'best_psnr' in checkpoint:
            print(f"Model validation PSNR: {checkpoint['best_psnr']:.2f} dB")
    
    model.eval()
    print("Model loaded!\n")
    
    # Get image list
    blur_images = sorted([f for f in os.listdir(args.blur_dir) if f.endswith(('.jpg', '.png'))])
    
    # Process samples
    total_psnr_blur = 0
    total_psnr_deblur = 0
    
    print(f"Creating {args.num_samples} comparisons...\n")
    
    for i, img_name in enumerate(blur_images[:args.num_samples]):
        blur_path = os.path.join(args.blur_dir, img_name)
        sharp_path = os.path.join(args.sharp_dir, img_name)
        
        if not os.path.exists(sharp_path):
            print(f"Warning: {sharp_path} not found, skipping...")
            continue
        
        output_path = os.path.join(args.output_dir, f'comparison_{i+1}.jpg')
        
        print(f"[{i+1}/{args.num_samples}] Processing: {img_name}")
        
        psnr_blur, psnr_deblur = create_comparison(
            blur_path, sharp_path, model, device, output_path
        )
        
        total_psnr_blur += psnr_blur
        total_psnr_deblur += psnr_deblur
        
        print(f"  Blur PSNR: {psnr_blur:.2f} dB")
        print(f"  Deblur PSNR: {psnr_deblur:.2f} dB")
        print(f"  Improvement: {psnr_deblur - psnr_blur:.2f} dB")
        print(f"  Saved: {output_path}\n")
    
    # Print summary
    avg_psnr_blur = total_psnr_blur / args.num_samples
    avg_psnr_deblur = total_psnr_deblur / args.num_samples
    
    print("=" * 50)
    print("SUMMARY")
    print("=" * 50)
    print(f"Average Blur PSNR: {avg_psnr_blur:.2f} dB")
    print(f"Average Deblur PSNR: {avg_psnr_deblur:.2f} dB")
    print(f"Average Improvement: {avg_psnr_deblur - avg_psnr_blur:.2f} dB")
    print(f"\n✓ Comparisons saved in: {args.output_dir}")


if __name__ == '__main__':
    main()
