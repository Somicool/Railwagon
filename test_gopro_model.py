"""
Test GoPro Pre-trained Model vs Fine-tuned Model
Quick comparison to see which performs better on railway images
"""
import torch
import cv2
import numpy as np
from pathlib import Path
import sys
sys.path.append('models')
from mimo_unet_plus import MIMOUNetPlus

def calculate_psnr(img1, img2):
    """Calculate PSNR between two images"""
    mse = np.mean((img1.astype(float) - img2.astype(float)) ** 2)
    if mse == 0:
        return 100
    return 20 * np.log10(255.0 / np.sqrt(mse))

def load_model(weights_path, device):
    """Load MIMOUNetPlus model"""
    print(f"Loading model: {weights_path}")
    model = MIMOUNetPlus()
    
    try:
        checkpoint = torch.load(weights_path, map_location=device)
        if isinstance(checkpoint, dict) and 'model_state_dict' in checkpoint:
            model.load_state_dict(checkpoint['model_state_dict'])
            print(f"  ✓ Loaded from checkpoint (epoch {checkpoint.get('epoch', 'unknown')})")
        else:
            model.load_state_dict(checkpoint)
            print(f"  ✓ Loaded state dict")
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return None
    
    model.to(device)
    model.eval()
    return model

def deblur_image(model, img, device):
    """Deblur a single image"""
    # Prepare image
    h, w = img.shape[:2]
    
    # Pad to multiple of 16
    pad_h = (16 - h % 16) % 16
    pad_w = (16 - w % 16) % 16
    img_padded = cv2.copyMakeBorder(img, 0, pad_h, 0, pad_w, cv2.BORDER_REFLECT)
    
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
    
    # Remove padding
    output = output[:h, :w]
    
    return output

def main():
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Using device: {device}\n")
    
    # Models to test
    models_to_test = {
        'GoPro Pre-trained': 'weights/gopro_pretrained.pth',
        'GoPro Best': 'weights/gopro_best.pth',
        'MIMOUNet+ GoPro': 'weights/mimo_unetplus_gopro_trained.pth',
        'Fine-tuned (ours)': 'checkpoints/best_model.pkl'
    }
    
    # Get test images from train dataset
    blur_dir = Path('train/train/blur')
    sharp_dir = Path('train/train/sharp')
    
    test_images = list(blur_dir.glob('*.jpg'))[:5]  # Test on 5 images
    
    if not test_images:
        print("No test images found in train/train/blur/")
        return
    
    print(f"Testing on {len(test_images)} railway images\n")
    print("="*70)
    
    results = {}
    
    # Test each model
    for model_name, weights_path in models_to_test.items():
        if not Path(weights_path).exists():
            print(f"\n{model_name}: SKIP - weights not found")
            continue
        
        print(f"\n{model_name}")
        print("-"*70)
        
        # Load model
        model = load_model(weights_path, device)
        if model is None:
            continue
        
        psnr_scores = []
        
        # Test on images
        for i, blur_path in enumerate(test_images, 1):
            # Load blur and sharp images
            blur_img = cv2.imread(str(blur_path))
            sharp_path = sharp_dir / blur_path.name
            
            if not sharp_path.exists():
                continue
            
            sharp_img = cv2.imread(str(sharp_path))
            
            # Deblur
            deblurred = deblur_image(model, blur_img, device)
            
            # Calculate PSNR
            psnr = calculate_psnr(deblurred, sharp_img)
            psnr_scores.append(psnr)
            
            print(f"  Image {i}: {psnr:.2f} dB")
        
        avg_psnr = np.mean(psnr_scores)
        results[model_name] = avg_psnr
        
        print(f"  Average: {avg_psnr:.2f} dB")
        
        # Save sample result
        if test_images:
            blur_img = cv2.imread(str(test_images[0]))
            deblurred = deblur_image(model, blur_img, device)
            sharp_img = cv2.imread(str(sharp_dir / test_images[0].name))
            
            # Create comparison
            comparison = np.hstack([blur_img, deblurred, sharp_img])
            output_name = f"comparison_{model_name.replace(' ', '_').replace('(', '').replace(')', '').lower()}.jpg"
            cv2.imwrite(output_name, comparison)
            print(f"  Saved: {output_name}")
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY - Average PSNR on Railway Images")
    print("="*70)
    
    sorted_results = sorted(results.items(), key=lambda x: x[1], reverse=True)
    for model_name, psnr in sorted_results:
        print(f"{model_name:30s}: {psnr:6.2f} dB")
    
    if sorted_results:
        best_model = sorted_results[0]
        print("\n" + "="*70)
        print(f"🏆 BEST MODEL: {best_model[0]} ({best_model[1]:.2f} dB)")
        print("="*70)
        
        # Find the weights path for best model
        best_weights = models_to_test[best_model[0]]
        print(f"\nRecommendation: Update pipeline to use '{best_weights}'")

if __name__ == '__main__':
    main()
