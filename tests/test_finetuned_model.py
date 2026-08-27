"""
Test fine-tuned MIMOUNetPlus model on sample images
"""

import os
import torch
import cv2
import numpy as np
from models.mimo_unet_plus import MIMOUNetPlus
import argparse


def load_image(image_path):
    """Load and preprocess image"""
    img = cv2.imread(image_path)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img_tensor = torch.from_numpy(img).float().permute(2, 0, 1) / 255.0
    img_tensor = img_tensor.unsqueeze(0)  # Add batch dimension
    return img_tensor, img.shape[:2]


def save_image(tensor, output_path):
    """Save tensor as image"""
    img = tensor.squeeze(0).permute(1, 2, 0).cpu().numpy()
    img = np.clip(img * 255.0, 0, 255).astype(np.uint8)
    img_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    cv2.imwrite(output_path, img_bgr)
    print(f"Saved: {output_path}")


def test_model(model_path, test_images, output_dir, device):
    """Test model on images"""
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Load model
    print(f"Loading model from: {model_path}")
    model = MIMOUNetPlus(num_res=8).to(device)
    
    if model_path.endswith('.pkl'):
        state_dict = torch.load(model_path, map_location=device)
        model.load_state_dict(state_dict)
    else:
        checkpoint = torch.load(model_path, map_location=device)
        model.load_state_dict(checkpoint['model_state_dict'])
        if 'best_psnr' in checkpoint:
            print(f"Model best PSNR: {checkpoint['best_psnr']:.2f} dB")
    
    model.eval()
    print("Model loaded successfully!\n")
    
    # Process images
    for img_path in test_images:
        if not os.path.exists(img_path):
            print(f"Warning: {img_path} not found, skipping...")
            continue
        
        print(f"Processing: {img_path}")
        
        # Load image
        img_tensor, original_size = load_image(img_path)
        img_tensor = img_tensor.to(device)
        
        # Inference
        with torch.no_grad():
            outputs = model(img_tensor)
            deblurred = outputs[0]  # Use full resolution output
        
        # Save result
        basename = os.path.basename(img_path)
        name, ext = os.path.splitext(basename)
        output_path = os.path.join(output_dir, f"{name}_deblurred{ext}")
        save_image(deblurred, output_path)
    
    print(f"\n✓ All images processed! Check: {output_dir}")


def main():
    parser = argparse.ArgumentParser(description='Test fine-tuned model')
    parser.add_argument('--model', type=str, required=True,
                        help='Path to model checkpoint (.pth or .pkl)')
    parser.add_argument('--images', type=str, nargs='+', required=True,
                        help='List of test images')
    parser.add_argument('--output', type=str, default='test_output_finetuned',
                        help='Output directory')
    
    args = parser.parse_args()
    
    # Device
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Using device: {device}\n")
    
    # Test model
    test_model(args.model, args.images, args.output, device)


if __name__ == '__main__':
    main()
