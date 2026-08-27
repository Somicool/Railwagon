"""
Test the improved model (29.86 dB) vs original (25.30 dB)
"""
import torch
import cv2
import numpy as np
from pathlib import Path
import sys
sys.path.append('models')
from mimo_unet_plus import MIMOUNetPlus

def deblur_image(model, image_path, device):
    """Deblur a single image"""
    # Load image
    img = cv2.imread(str(image_path))
    h, w = img.shape[:2]
    
    # Pad to multiple of 16
    pad_h = (16 - h % 16) % 16
    pad_w = (16 - w % 16) % 16
    img_padded = cv2.copyMakeBorder(img, 0, pad_h, 0, pad_w, cv2.BORDER_REFLECT)
    
    # To tensor
    img_tensor = torch.from_numpy(img_padded).permute(2, 0, 1).float() / 255.0
    img_tensor = img_tensor.unsqueeze(0).to(device)
    
    # Deblur
    with torch.no_grad():
        output = model(img_tensor)
        if isinstance(output, (list, tuple)):
            output = output[0]
    
    # To numpy
    output = output.squeeze(0).permute(1, 2, 0).cpu().numpy()
    output = np.clip(output * 255, 0, 255).astype(np.uint8)
    
    # Remove padding
    output = output[:h, :w]
    
    return output

def calculate_psnr(img1, img2):
    """Calculate PSNR between two images"""
    mse = np.mean((img1.astype(float) - img2.astype(float)) ** 2)
    if mse == 0:
        return float('inf')
    return 20 * np.log10(255.0 / np.sqrt(mse))

def main():
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Device: {device}\n")
    
    # Load both models
    print("Loading models...")
    old_model = MIMOUNetPlus().to(device)
    new_model = MIMOUNetPlus().to(device)
    
    old_model.load_state_dict(torch.load('checkpoints/best_model.pkl'))
    new_model.load_state_dict(torch.load('checkpoints/best_model_improved.pkl'))
    
    old_model.eval()
    new_model.eval()
    print("✓ Models loaded\n")
    
    # Get test images
    blur_dir = Path('train/train/blur')
    sharp_dir = Path('train/train/sharp')
    blur_images = sorted(list(blur_dir.glob('*.jpg')))[:10]  # Test on 10 images
    
    print("Testing on 10 images:")
    print("=" * 70)
    
    old_psnrs = []
    new_psnrs = []
    improvements = []
    
    for i, blur_path in enumerate(blur_images, 1):
        # Get corresponding sharp image
        sharp_path = sharp_dir / blur_path.name
        sharp_img = cv2.imread(str(sharp_path))
        
        # Deblur with both models
        old_deblurred = deblur_image(old_model, blur_path, device)
        new_deblurred = deblur_image(new_model, blur_path, device)
        
        # Calculate PSNR
        old_psnr = calculate_psnr(old_deblurred, sharp_img)
        new_psnr = calculate_psnr(new_deblurred, sharp_img)
        improvement = new_psnr - old_psnr
        
        old_psnrs.append(old_psnr)
        new_psnrs.append(new_psnr)
        improvements.append(improvement)
        
        print(f"{i:2d}. {blur_path.name:20s}  Old: {old_psnr:5.2f} dB  New: {new_psnr:5.2f} dB  Δ: {improvement:+5.2f} dB")
        
        # Save comparison for first image
        if i == 1:
            blur_img = cv2.imread(str(blur_path))
            comparison = np.hstack([blur_img, old_deblurred, new_deblurred, sharp_img])
            cv2.imwrite('comparison_old_vs_new.jpg', comparison)
            print(f"    → Saved comparison: comparison_old_vs_new.jpg")
    
    print("=" * 70)
    print(f"\nAverage PSNR:")
    print(f"  Old Model (25.30 dB trained): {np.mean(old_psnrs):.2f} dB")
    print(f"  New Model (29.86 dB trained): {np.mean(new_psnrs):.2f} dB")
    print(f"  Average Improvement:          {np.mean(improvements):+.2f} dB")
    print(f"\nBest improvement: {max(improvements):+.2f} dB")
    print(f"Worst improvement: {min(improvements):+.2f} dB")
    
    print("\n" + "=" * 70)
    print("CONCLUSION:")
    if np.mean(improvements) > 2:
        print(f"  ✓ EXCELLENT! New model is {np.mean(improvements):.2f} dB better!")
        print(f"    This is a significant quality improvement.")
    elif np.mean(improvements) > 1:
        print(f"  ✓ GOOD! New model is {np.mean(improvements):.2f} dB better.")
    else:
        print(f"  ~ Minor improvement of {np.mean(improvements):.2f} dB.")
    print("=" * 70)

if __name__ == '__main__':
    main()
