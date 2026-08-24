"""
Quick dataset check and visualization
Verify dataset is ready for training
"""

import os
import cv2
import numpy as np
from PIL import Image


def check_dataset(blur_dir, sharp_dir):
    """Check dataset integrity"""
    
    print("=" * 60)
    print("DATASET CHECK")
    print("=" * 60)
    
    # Check directories exist
    if not os.path.exists(blur_dir):
        print(f"❌ Blur directory not found: {blur_dir}")
        return False
    
    if not os.path.exists(sharp_dir):
        print(f"❌ Sharp directory not found: {sharp_dir}")
        return False
    
    print(f"✓ Blur directory: {blur_dir}")
    print(f"✓ Sharp directory: {sharp_dir}")
    print()
    
    # Get file lists
    blur_files = sorted([f for f in os.listdir(blur_dir) if f.endswith(('.jpg', '.png', '.jpeg'))])
    sharp_files = sorted([f for f in os.listdir(sharp_dir) if f.endswith(('.jpg', '.png', '.jpeg'))])
    
    print(f"Blur images: {len(blur_files)}")
    print(f"Sharp images: {len(sharp_files)}")
    print()
    
    # Check counts match
    if len(blur_files) != len(sharp_files):
        print(f"⚠️  Warning: Image count mismatch!")
        print(f"   Blur: {len(blur_files)}, Sharp: {len(sharp_files)}")
    else:
        print(f"✓ Image counts match: {len(blur_files)} pairs")
    print()
    
    # Check file names match
    mismatches = []
    for blur_file in blur_files[:100]:  # Check first 100
        if blur_file not in sharp_files:
            mismatches.append(blur_file)
    
    if mismatches:
        print(f"⚠️  Warning: {len(mismatches)} filename mismatches found")
        print(f"   Examples: {mismatches[:5]}")
    else:
        print("✓ File names match (checked first 100)")
    print()
    
    # Check sample images
    print("Checking sample images...")
    sample_blur = os.path.join(blur_dir, blur_files[0])
    sample_sharp = os.path.join(sharp_dir, sharp_files[0])
    
    try:
        blur_img = Image.open(sample_blur)
        sharp_img = Image.open(sample_sharp)
        
        print(f"✓ Sample blur image: {blur_img.size} - {blur_img.mode}")
        print(f"✓ Sample sharp image: {sharp_img.size} - {sharp_img.mode}")
        
        if blur_img.size != sharp_img.size:
            print(f"⚠️  Warning: Image sizes don't match!")
        else:
            print(f"✓ Image sizes match: {blur_img.size}")
        
    except Exception as e:
        print(f"❌ Error loading images: {e}")
        return False
    
    print()
    
    # Calculate dataset statistics
    print("Dataset Statistics:")
    print("-" * 60)
    
    sizes = []
    for i, blur_file in enumerate(blur_files[:50]):  # Sample 50 images
        img_path = os.path.join(blur_dir, blur_file)
        try:
            img = Image.open(img_path)
            sizes.append(img.size)
        except:
            continue
    
    if sizes:
        widths = [s[0] for s in sizes]
        heights = [s[1] for s in sizes]
        
        print(f"Image width:  min={min(widths)}, max={max(widths)}, avg={int(np.mean(widths))}")
        print(f"Image height: min={min(heights)}, max={max(heights)}, avg={int(np.mean(heights))}")
    
    print()
    print("=" * 60)
    print("DATASET READY FOR TRAINING!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Run: python finetune_mimo.py")
    print("2. Or:  START_FINETUNING.bat")
    print()
    
    return True


def create_sample_visualization(blur_dir, sharp_dir, output_file='dataset_sample.jpg'):
    """Create a visualization of sample pairs"""
    
    print(f"Creating sample visualization: {output_file}")
    
    blur_files = sorted([f for f in os.listdir(blur_dir) if f.endswith(('.jpg', '.png'))])
    
    samples = []
    for i in range(min(3, len(blur_files))):
        blur_path = os.path.join(blur_dir, blur_files[i])
        sharp_path = os.path.join(sharp_dir, blur_files[i])
        
        blur_img = cv2.imread(blur_path)
        sharp_img = cv2.imread(sharp_path)
        
        # Resize to standard size
        h, w = 200, 300
        blur_resized = cv2.resize(blur_img, (w, h))
        sharp_resized = cv2.resize(sharp_img, (w, h))
        
        # Add labels
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(blur_resized, 'Blur', (10, 30), font, 0.8, (0, 255, 255), 2)
        cv2.putText(sharp_resized, 'Sharp', (10, 30), font, 0.8, (0, 255, 0), 2)
        
        # Concatenate pair
        pair = np.hstack([blur_resized, sharp_resized])
        samples.append(pair)
    
    # Stack all samples vertically
    if samples:
        result = np.vstack(samples)
        cv2.imwrite(output_file, result)
        print(f"✓ Saved: {output_file}")
        print()


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Check dataset')
    parser.add_argument('--blur_dir', type=str, default='train/train/blur')
    parser.add_argument('--sharp_dir', type=str, default='train/train/sharp')
    parser.add_argument('--visualize', action='store_true', help='Create sample visualization')
    
    args = parser.parse_args()
    
    # Check dataset
    check_dataset(args.blur_dir, args.sharp_dir)
    
    # Create visualization if requested
    if args.visualize:
        create_sample_visualization(args.blur_dir, args.sharp_dir)
