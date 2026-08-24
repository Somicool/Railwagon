"""
Use fine-tuned MIMOUNetPlus model for deblurring
Production-ready script
"""

import cv2
import numpy as np
import torch
from models.mimo_unet_plus import MIMOUNetPlus
import argparse
import os


def deblur_image(image_path, model, device):
    """Deblur a single image"""
    # Load image
    img = cv2.imread(image_path)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
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
    
    # Remove padding
    deblurred = deblurred[:h, :w]
    
    # Convert back to BGR
    deblurred_bgr = cv2.cvtColor(deblurred, cv2.COLOR_RGB2BGR)
    
    return deblurred_bgr


def main():
    parser = argparse.ArgumentParser(description='Deblur with fine-tuned model')
    parser.add_argument('--input', type=str, required=True, help='Input image path')
    parser.add_argument('--output', type=str, default=None, help='Output path (default: input_deblurred.jpg)')
    parser.add_argument('--model', type=str, default='checkpoints/best_model.pkl', help='Model path')
    
    args = parser.parse_args()
    
    # Set output path
    if args.output is None:
        name, ext = os.path.splitext(args.input)
        args.output = f"{name}_deblurred{ext}"
    
    # Device
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Using device: {device}")
    
    # Load model
    print(f"Loading model: {args.model}")
    model = MIMOUNetPlus(num_res=8).to(device)
    model.load_state_dict(torch.load(args.model, map_location=device))
    model.eval()
    print("Model loaded!")
    
    # Deblur
    print(f"Processing: {args.input}")
    result = deblur_image(args.input, model, device)
    
    # Save
    cv2.imwrite(args.output, result)
    print(f"✓ Saved: {args.output}")


if __name__ == '__main__':
    main()
