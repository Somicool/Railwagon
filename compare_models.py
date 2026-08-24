"""
Compare Pretrained vs Fine-tuned Model Performance
Side-by-side comparison on the same images
"""

import cv2
import numpy as np
import torch
from models.mimo_unet_plus import MIMOUNetPlus
import os
from pathlib import Path


def deblur_with_model(image, model, device):
    """Deblur image with given model"""
    img_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    h, w = img_rgb.shape[:2]
    
    # Pad to multiple of 16
    pad_h = (16 - h % 16) % 16
    pad_w = (16 - w % 16) % 16
    img_padded = np.pad(img_rgb, ((0, pad_h), (0, pad_w), (0, 0)), mode='reflect')
    
    # Convert to tensor
    img_tensor = torch.from_numpy(img_padded).float().permute(2, 0, 1) / 255.0
    img_tensor = img_tensor.unsqueeze(0).to(device)
    
    # Deblur
    with torch.no_grad():
        outputs = model(img_tensor)
        deblurred = outputs[0].squeeze(0).permute(1, 2, 0).cpu().numpy()
        deblurred = np.clip(deblurred * 255.0, 0, 255).astype(np.uint8)
    
    # Remove padding and convert to BGR
    deblurred = deblurred[:h, :w]
    deblurred_bgr = cv2.cvtColor(deblurred, cv2.COLOR_RGB2BGR)
    
    return deblurred_bgr


def create_comparison(image_path, pretrained_path, finetuned_path, output_path, device):
    """Create side-by-side comparison"""
    
    # Load models
    print(f"Loading pretrained model: {pretrained_path}")
    pretrained_model = MIMOUNetPlus().to(device)
    pretrained_model.load_state_dict(torch.load(pretrained_path, map_location=device))
    pretrained_model.eval()
    
    print(f"Loading fine-tuned model: {finetuned_path}")
    finetuned_model = MIMOUNetPlus().to(device)
    checkpoint = torch.load(finetuned_path, map_location=device)
    if isinstance(checkpoint, dict) and 'model_state_dict' in checkpoint:
        finetuned_model.load_state_dict(checkpoint['model_state_dict'])
    else:
        finetuned_model.load_state_dict(checkpoint)
    finetuned_model.eval()
    
    # Load image
    print(f"\nProcessing: {image_path}")
    img = cv2.imread(image_path)
    
    # Deblur with both models
    print("  Deblurring with pretrained model...")
    pretrained_result = deblur_with_model(img, pretrained_model, device)
    
    print("  Deblurring with fine-tuned model...")
    finetuned_result = deblur_with_model(img, finetuned_model, device)
    
    # Resize for display
    h, w = img.shape[:2]
    display_h = min(h, 400)
    display_w = int(w * display_h / h)
    
    original_resized = cv2.resize(img, (display_w, display_h))
    pretrained_resized = cv2.resize(pretrained_result, (display_w, display_h))
    finetuned_resized = cv2.resize(finetuned_result, (display_w, display_h))
    
    # Add labels
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.7
    thickness = 2
    color = (255, 255, 255)
    
    cv2.putText(original_resized, 'Original (Blur)', (10, 30), font, font_scale, color, thickness)
    cv2.putText(pretrained_resized, 'Pretrained Model', (10, 30), font, font_scale, (0, 255, 255), thickness)
    cv2.putText(finetuned_resized, 'Fine-tuned Model', (10, 30), font, font_scale, (0, 255, 0), thickness)
    
    # Concatenate horizontally
    comparison = np.hstack([original_resized, pretrained_resized, finetuned_resized])
    
    # Save
    cv2.imwrite(output_path, comparison)
    print(f"  ✓ Saved: {output_path}\n")
    
    return comparison


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Compare pretrained vs fine-tuned models')
    parser.add_argument('--image', type=str, required=True, help='Input image')
    parser.add_argument('--pretrained', type=str, default='weights/MIMO-UNetPlus.pkl', 
                        help='Pretrained model path')
    parser.add_argument('--finetuned', type=str, default='checkpoints/best_model.pkl',
                        help='Fine-tuned model path')
    parser.add_argument('--output', type=str, default='model_comparison.jpg',
                        help='Output comparison image')
    
    args = parser.parse_args()
    
    # Device
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Using device: {device}\n")
    
    # Create comparison
    create_comparison(args.image, args.pretrained, args.finetuned, args.output, device)
    
    print("="*60)
    print("COMPARISON COMPLETE")
    print("="*60)
    print(f"View the side-by-side comparison: {args.output}")
    print("\nLeft:   Original blur")
    print("Center: Pretrained model result")
    print("Right:  Fine-tuned model result")
    print("="*60)


if __name__ == '__main__':
    main()
