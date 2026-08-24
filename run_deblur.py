"""
Image Deblurring Inference Script
----------------------------------
Simple script to deblur a single image using the MIMO-UNet model

Usage:
    python run_deblur.py --input path/to/blurry_image.jpg --output deblurred.jpg

Requirements:
    - PyTorch
    - OpenCV (cv2)
    - NumPy
    - Pretrained weights in weights/mimo_unet.pth
"""

import argparse
import os
import cv2
import numpy as np
import torch
from models.mimo_official import create_model


def load_image(image_path):
    """
    Load and preprocess an image for MIMO-UNet
    
    Args:
        image_path: Path to the input image
    
    Returns:
        - Preprocessed tensor ready for model [1, 3, H, W]
        - Original image shape for resizing back
        - Original image for reference
    """
    # Read image using OpenCV (BGR format)
    img = cv2.imread(image_path)
    
    if img is None:
        raise ValueError(f"Could not read image from {image_path}")
    
    # Store original dimensions
    original_shape = img.shape[:2]  # (H, W)
    original_img = img.copy()
    
    # Resize to dimensions divisible by 8 (MIMO-UNet downsamples by 4x)
    h, w = img.shape[:2]
    new_h = (h // 8) * 8
    new_w = (w // 8) * 8
    
    if (h, w) != (new_h, new_w):
        img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
    
    # Convert BGR to RGB
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    # Normalize to [0, 1] range (official MIMO-UNet preprocessing)
    img_normalized = img_rgb.astype(np.float32) / 255.0
    
    # Convert to PyTorch tensor: [H, W, C] -> [C, H, W]
    img_tensor = torch.from_numpy(img_normalized).permute(2, 0, 1)
    
    # Add batch dimension: [C, H, W] -> [1, C, H, W]
    img_tensor = img_tensor.unsqueeze(0)
    
    return img_tensor, original_shape, original_img


def save_image(tensor, output_path, original_shape):
    """
    Convert model output tensor back to image and save
    
    Args:
        tensor: Output from model [1, 3, H, W] in range [0, 1]
        output_path: Path to save the deblurred image
        original_shape: Original image shape (H, W) to resize back to
    """
    # Remove batch dimension: [1, 3, H, W] -> [3, H, W]
    img = tensor.squeeze(0)
    
    # Convert to numpy and transpose: [3, H, W] -> [H, W, 3]
    img = img.permute(1, 2, 0).cpu().numpy()
    
    # Clip to [0, 1] and add small bias (from official implementation)
    img = np.clip(img, 0, 1)
    img = img + 0.5 / 255.0  # Small bias from official code
    img = np.clip(img, 0, 1)
    
    # Convert to [0, 255]
    img = (img * 255.0).astype(np.uint8)
    
    # Resize back to original dimensions if needed
    if img.shape[:2] != original_shape:
        img = cv2.resize(img, (original_shape[1], original_shape[0]), interpolation=cv2.INTER_CUBIC)
    
    # Convert RGB to BGR for OpenCV
    img_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    
    # Save the image
    cv2.imwrite(output_path, img_bgr)
    print(f"✓ Saved deblurred image to: {output_path}")


def load_model_weights(model, weights_path, device):
    """
    Load pretrained weights into the model
    
    Args:
        model: The MIMO-UNet model instance
        weights_path: Path to the .pth weights file
        device: Device to load the model on (cpu/cuda)
    
    Returns:
        Model with loaded weights
    """
    if not os.path.exists(weights_path):
        print(f"⚠ Warning: Weights file not found at {weights_path}")
        print("The model will run with random weights (for testing only).")
        print("\nTo use pretrained weights:")
        print("1. Download or train a model")
        print("2. Save weights as 'weights/mimo_unet.pth'")
        return model
    
    # Load the state dict
    checkpoint = torch.load(weights_path, map_location=device, weights_only=False)
    
    # Handle different checkpoint formats
    if isinstance(checkpoint, dict) and 'model' in checkpoint:
        state_dict = checkpoint['model']
    elif isinstance(checkpoint, dict) and 'model_state_dict' in checkpoint:
        state_dict = checkpoint['model_state_dict']
    else:
        state_dict = checkpoint
    
    # Load weights into model
    missing, unexpected = model.load_state_dict(state_dict, strict=False)
    loaded_keys = len(state_dict) - len(missing)
    total_keys = len(state_dict)
    print(f"✓ Loaded {loaded_keys}/{total_keys} weight parameters")
    if len(missing) > 0:
        print(f"  Missing: {len(missing)} parameters")
    if len(unexpected) > 0:
        print(f"  Unexpected: {len(unexpected)} parameters (ignored)")
    print(f"✓ Loaded pretrained weights from: {weights_path}")
    
    return model


def deblur_image(input_path, output_path, weights_path='weights/lol_epoch_20.pth'):
    """
    Main function to deblur an image
    
    Args:
        input_path: Path to blurry input image
        output_path: Path to save deblurred output
        weights_path: Path to pretrained model weights
    """
    print("=" * 60)
    print("MIMO-UNet Image Deblurring")
    print("=" * 60)
    
    # 1. Setup device (GPU if available, otherwise CPU)
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Using device: {device}")
    
    # 2. Create the model
    print("\nLoading model architecture...")
    model = create_model('MIMO-UNetPlus')  # Use Plus version for these weights
    model = model.to(device)
    
    # 3. Load pretrained weights
    print("Loading weights...")
    model = load_model_weights(model, weights_path, device)
    
    # 4. Set model to evaluation mode (disables dropout, batch norm in training mode)
    model.eval()
    
    # 5. Load and preprocess the input image
    print(f"\nLoading image: {input_path}")
    img_tensor, original_shape, original_img = load_image(input_path)
    img_tensor = img_tensor.to(device)
    
    print(f"Image shape: {original_img.shape}")
    print(f"Tensor shape: {img_tensor.shape}")
    
    # 6. Run inference (no gradient computation needed)
    print("\nRunning deblurring inference...")
    with torch.no_grad():
        outputs = model(img_tensor)
        # MIMO-UNet returns 3 scales: [coarse, medium, fine]
        # Use the finest scale (last output)
        output_tensor = outputs[-1] if isinstance(outputs, list) else outputs
    
    # 7. Save the deblurred image
    print("Saving result...")
    save_image(output_tensor, output_path, original_shape)
    
    print("\n" + "=" * 60)
    print("Deblurring complete!")
    print("=" * 60)


def main():
    """
    Parse command line arguments and run deblurring
    """
    parser = argparse.ArgumentParser(
        description='Deblur an image using MIMO-UNet',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Basic usage
    python run_deblur.py --input blurry.jpg --output sharp.jpg
    
    # With custom weights path
    python run_deblur.py --input blurry.jpg --output sharp.jpg --weights my_weights.pth
        """
    )
    
    parser.add_argument(
        '--input', '-i',
        type=str,
        required=True,
        help='Path to the blurry input image'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        required=True,
        help='Path to save the deblurred output image'
    )
    
    parser.add_argument(
        '--weights', '-w',
        type=str,
        default='checkpoints/best_model.pkl',
        help='Path to model weights (default: checkpoints/best_model.pkl - fine-tuned)'
    )
    
    args = parser.parse_args()
    
    # Verify input file exists
    if not os.path.exists(args.input):
        print(f"Error: Input file not found: {args.input}")
        return
    
    # Create output directory if it doesn't exist
    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")
    
    # Run deblurring
    deblur_image(args.input, args.output, args.weights)


if __name__ == "__main__":
    main()
