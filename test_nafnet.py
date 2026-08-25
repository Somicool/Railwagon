"""
Test NAFNet on railway images and compare with current model
"""
import torch
import cv2
import numpy as np
from pathlib import Path
import sys
sys.path.append('models')

def calculate_psnr(img1, img2):
    """Calculate PSNR between two images"""
    mse = np.mean((img1.astype(float) - img2.astype(float)) ** 2)
    if mse == 0:
        return 100
    return 20 * np.log10(255.0 / np.sqrt(mse))

def load_nafnet():
    """Load NAFNet model"""
    from nafnet import NAFNetLocal
    
    model = NAFNetLocal()
    weights_path = 'weights/nafnet_gopro.pth'
    
    if Path(weights_path).exists():
        print(f"Loading NAFNet weights from {weights_path}")
        try:
            checkpoint = torch.load(weights_path, map_location='cpu', weights_only=False)
            if 'params' in checkpoint:
                model.load_state_dict(checkpoint['params'])
            elif 'state_dict' in checkpoint:
                model.load_state_dict(checkpoint['state_dict'])
            else:
                model.load_state_dict(checkpoint)
            print("✓ Loaded pretrained NAFNet")
        except Exception as e:
            print(f"⚠ Could not load pretrained weights: {e}")
            print("  Using random initialization (will not work well)")
    else:
        print(f"⚠ Pretrained weights not found at {weights_path}")
        print("  Downloading from alternative source...")
        
        # Try alternative download
        try:
            import urllib.request
            url = "https://github.com/megvii-research/NAFNet/releases/download/v1.0/NAFNet-GoPro-width32.pth"
            print(f"  Downloading from {url}")
            urllib.request.urlretrieve(url, weights_path)
            print(f"  ✓ Downloaded to {weights_path}")
            
            checkpoint = torch.load(weights_path, map_location='cpu')
            if 'params' in checkpoint:
                model.load_state_dict(checkpoint['params'])
            else:
                model.load_state_dict(checkpoint)
            print("  ✓ Loaded pretrained NAFNet")
        except Exception as e:
            print(f"  ✗ Download failed: {e}")
            print("\n  Please download manually:")
            print("  https://github.com/megvii-research/NAFNet/releases/download/v1.0/NAFNet-GoPro-width32.pth")
            print(f"  Save to: {Path(weights_path).absolute()}")
            return None
    
    return model

def load_mimo_unet():
    """Load current MIMOUNetPlus model"""
    from mimo_unet_plus import MIMOUNetPlus
    
    model = MIMOUNetPlus()
    checkpoint = torch.load('checkpoints/best_model.pkl', map_location='cpu')
    model.load_state_dict(checkpoint)
    
    return model

def deblur_image(model, img, device, pad_to_multiple=None):
    """Deblur a single image"""
    h, w = img.shape[:2]
    
    # Pad to multiple if needed (for MIMO models)
    if pad_to_multiple:
        pad_h = (pad_to_multiple - h % pad_to_multiple) % pad_to_multiple
        pad_w = (pad_to_multiple - w % pad_to_multiple) % pad_to_multiple
        img_padded = cv2.copyMakeBorder(img, 0, pad_h, 0, pad_w, cv2.BORDER_REFLECT)
    else:
        img_padded = img
    
    # Convert to tensor
    img_tensor = torch.from_numpy(img_padded).permute(2, 0, 1).float() / 255.0
    img_tensor = img_tensor.unsqueeze(0).to(device)
    
    # Deblur
    with torch.no_grad():
        output = model(img_tensor)
        if isinstance(output, (list, tuple)):
            output = output[0]
    
    # Convert back to image
    output = output.squeeze(0).permute(1, 2, 0).cpu().numpy()
    output = np.clip(output * 255.0, 0, 255).astype(np.uint8)
    
    # Crop to original size
    output = output[:h, :w]
    
    return output

def main():
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Using device: {device}\n")
    
    # Load models
    print("="*70)
    print("LOADING MODELS")
    print("="*70)
    
    print("\n1. Loading NAFNet...")
    nafnet = load_nafnet()
    if nafnet is None:
        print("\n✗ Could not load NAFNet. Exiting.")
        return
    nafnet = nafnet.to(device)
    nafnet.eval()
    
    print("\n2. Loading current MIMOUNetPlus...")
    mimo = load_mimo_unet()
    mimo = mimo.to(device)
    mimo.eval()
    
    # Get test images
    blur_dir = Path('train/train/blur')
    sharp_dir = Path('train/train/sharp')
    
    test_images = list(blur_dir.glob('*.jpg'))[:5]
    
    if not test_images:
        print("\n✗ No test images found")
        return
    
    print(f"\nTesting on {len(test_images)} railway images")
    print("="*70)
    
    # Test both models
    results = {'NAFNet': [], 'MIMOUNetPlus (current)': []}
    
    for i, blur_path in enumerate(test_images, 1):
        blur_img = cv2.imread(str(blur_path))
        sharp_path = sharp_dir / blur_path.name
        
        if not sharp_path.exists():
            continue
        
        sharp_img = cv2.imread(str(sharp_path))
        
        print(f"\nImage {i}: {blur_path.name}")
        print("-"*70)
        
        # Test NAFNet (no padding needed)
        deblurred_naf = deblur_image(nafnet, blur_img, device)
        psnr_naf = calculate_psnr(deblurred_naf, sharp_img)
        results['NAFNet'].append(psnr_naf)
        print(f"  NAFNet:           {psnr_naf:.2f} dB")
        
        # Test MIMO (needs padding to multiple of 16)
        deblurred_mimo = deblur_image(mimo, blur_img, device, pad_to_multiple=16)
        psnr_mimo = calculate_psnr(deblurred_mimo, sharp_img)
        results['MIMOUNetPlus (current)'].append(psnr_mimo)
        print(f"  MIMOUNetPlus:     {psnr_mimo:.2f} dB")
        
        improvement = psnr_naf - psnr_mimo
        print(f"  Improvement:      {improvement:+.2f} dB")
        
        # Save comparison for first image
        if i == 1:
            comparison = np.hstack([blur_img, deblurred_mimo, deblurred_naf, sharp_img])
            # Add labels
            h, w = blur_img.shape[:2]
            comparison_labeled = comparison.copy()
            font = cv2.FONT_HERSHEY_SIMPLEX
            cv2.putText(comparison_labeled, 'Blur', (10, 30), font, 1, (0, 255, 0), 2)
            cv2.putText(comparison_labeled, f'MIMO ({psnr_mimo:.1f}dB)', (w+10, 30), font, 1, (0, 165, 255), 2)
            cv2.putText(comparison_labeled, f'NAFNet ({psnr_naf:.1f}dB)', (2*w+10, 30), font, 1, (0, 255, 0), 2)
            cv2.putText(comparison_labeled, 'Sharp', (3*w+10, 30), font, 1, (255, 255, 255), 2)
            
            cv2.imwrite('comparison_nafnet_vs_mimo.jpg', comparison_labeled)
            print(f"  Saved comparison to: comparison_nafnet_vs_mimo.jpg")
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY - Average PSNR on Railway Images")
    print("="*70)
    
    for model_name, psnrs in results.items():
        if psnrs:
            avg = np.mean(psnrs)
            print(f"{model_name:30s}: {avg:6.2f} dB")
    
    if results['NAFNet'] and results['MIMOUNetPlus (current)']:
        improvement = np.mean(results['NAFNet']) - np.mean(results['MIMOUNetPlus (current)'])
        print("\n" + "="*70)
        print(f"🎯 NAFNet is {improvement:+.2f} dB better than current model")
        print("="*70)
        
        if improvement > 2:
            print("\n✓ RECOMMENDATION: Switch to NAFNet for production use")
            print("  The quality improvement will be very noticeable!")
        elif improvement > 0:
            print("\n✓ NAFNet shows improvement, recommended for better quality")
        else:
            print("\n  Current model performs similarly, both are usable")

if __name__ == '__main__':
    main()
