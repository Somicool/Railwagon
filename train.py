"""
MIMO-UNetPlus Fine-Tuning Script for Wagon Dataset
===================================================
Fine-tunes pre-trained MIMO-UNetPlus model on custom wagon dataset.

Hardware: NVIDIA RTX 3050 6GB Laptop GPU
Dataset: Custom wagon images (blur → sharp)
Strategy: Fine-tuning from GoPro pre-trained weights
"""

import os
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import cv2
import numpy as np
from glob import glob
import random
from models.mimo_official import MIMOUNetPlus


# ============================================================================
# DATASET CLASS
# ============================================================================

class WagonDataset(Dataset):
    """
    Custom Wagon Dataset loader for deblurring.
    
    Structure:
        train/blur/image1.png
        train/sharp/image1.png
    """
    
    def __init__(self, root_dir='train/train', crop_size=256):
        """
        Args:
            root_dir (str): Path to dataset folder containing blur/ and sharp/
            crop_size (int): Random crop size (256x256)
        """
        self.crop_size = crop_size
        self.blur_dir = os.path.join(root_dir, 'blur')
        self.sharp_dir = os.path.join(root_dir, 'sharp')
        
        # Get all blur images
        self.blur_images = sorted(glob(os.path.join(self.blur_dir, '*.*')))
        
        print(f"\n{'='*70}")
        print(f"Loading wagon dataset from: {root_dir}")
        print(f"{'='*70}")
        print(f"Blur images found: {len(self.blur_images)}")
        
        # Match sharp images by filename
        self.sharp_images = []
        for blur_path in self.blur_images:
            filename = os.path.basename(blur_path)
            sharp_path = os.path.join(self.sharp_dir, filename)
            
            if os.path.exists(sharp_path):
                self.sharp_images.append(sharp_path)
            else:
                print(f"Warning: No matching sharp image for {filename}")
        
        print(f"✓ Valid image pairs: {len(self.sharp_images)}")
        print(f"{'='*70}\n")
        
        if len(self.sharp_images) == 0:
            raise ValueError(f"No valid image pairs found in {root_dir}")
        
        # Keep only matched pairs
        self.blur_images = self.blur_images[:len(self.sharp_images)]
    
    def __len__(self):
        return len(self.blur_images)
    
    def random_crop(self, blur, sharp):
        """
        Random crop for data augmentation.
        
        Args:
            blur: Blurry image [H, W, C]
            sharp: Sharp image [H, W, C]
        
        Returns:
            Cropped blur and sharp images
        """
        h, w = blur.shape[:2]
        
        if h < self.crop_size or w < self.crop_size:
            # Resize if image is smaller than crop size
            scale = max(self.crop_size / h, self.crop_size / w) * 1.1
            new_h, new_w = int(h * scale), int(w * scale)
            blur = cv2.resize(blur, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
            sharp = cv2.resize(sharp, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
            h, w = new_h, new_w
        
        # Random crop coordinates
        top = random.randint(0, h - self.crop_size)
        left = random.randint(0, w - self.crop_size)
        
        blur_crop = blur[top:top+self.crop_size, left:left+self.crop_size]
        sharp_crop = sharp[top:top+self.crop_size, left:left+self.crop_size]
        
        return blur_crop, sharp_crop
    
    def __getitem__(self, idx):
        """
        Get a single training sample.
        
        Returns:
            blur_tensor: [3, H, W] normalized to [0, 1]
            sharp_tensor: [3, H, W] normalized to [0, 1]
        """
        # Load images
        blur = cv2.imread(self.blur_images[idx])
        sharp = cv2.imread(self.sharp_images[idx])
        
        # Convert BGR to RGB
        blur = cv2.cvtColor(blur, cv2.COLOR_BGR2RGB)
        sharp = cv2.cvtColor(sharp, cv2.COLOR_BGR2RGB)
        
        # Random crop
        blur, sharp = self.random_crop(blur, sharp)
        
        # Convert to float and normalize to [0, 1]
        blur = blur.astype(np.float32) / 255.0
        sharp = sharp.astype(np.float32) / 255.0
        
        # Convert to PyTorch tensors [C, H, W]
        blur = torch.from_numpy(blur.transpose(2, 0, 1))
        sharp = torch.from_numpy(sharp.transpose(2, 0, 1))
        
        return blur, sharp


# ============================================================================
# TRAINING FUNCTION
# ============================================================================

def train_epoch(model, dataloader, criterion, optimizer, device, epoch):
    """
    Train for one epoch.
    
    Args:
        model: MIMO-UNetPlus model
        dataloader: Training data loader
        criterion: Loss function (L1Loss)
        optimizer: Adam optimizer
        device: CUDA or CPU
        epoch: Current epoch number
    
    Returns:
        Average loss for the epoch
    """
    model.train()
    epoch_loss = 0.0
    num_batches = len(dataloader)
    
    for batch_idx, (blur, sharp) in enumerate(dataloader):
        # Move data to device
        blur = blur.to(device)
        sharp = sharp.to(device)
        
        # Zero gradients
        optimizer.zero_grad()
        
        # Forward pass
        outputs = model(blur)
        
        # MIMO-UNetPlus returns 3 outputs at different scales
        # We use all 3 for multi-scale supervision
        if isinstance(outputs, list) or isinstance(outputs, tuple):
            # Multi-scale loss - resize outputs to match target size
            loss = 0
            for out in outputs:
                if out.shape != sharp.shape:
                    # Resize output to match target size
                    out_resized = torch.nn.functional.interpolate(
                        out, size=sharp.shape[2:], mode='bilinear', align_corners=False
                    )
                    loss += criterion(out_resized, sharp)
                else:
                    loss += criterion(out, sharp)
        else:
            # Single output
            loss = criterion(outputs, sharp)
        
        # Backward pass
        loss.backward()
        optimizer.step()
        
        # Accumulate loss
        epoch_loss += loss.item()
        
        # Print progress every 10 batches
        if (batch_idx + 1) % 10 == 0 or (batch_idx + 1) == num_batches:
            print(f"  Batch [{batch_idx+1}/{num_batches}] | Loss: {loss.item():.4f}")
    
    avg_loss = epoch_loss / num_batches
    return avg_loss


# ============================================================================
# MAIN TRAINING SCRIPT
# ============================================================================

def main():
    print("\n" + "="*70)
    print("MIMO-UNetPlus Fine-Tuning on Wagon Dataset")
    print("="*70)
    
    # -------------------------------------------------------------------------
    # DEVICE SETUP
    # -------------------------------------------------------------------------
    
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"\n✓ Device: {device}")
    
    if torch.cuda.is_available():
        print(f"  GPU: {torch.cuda.get_device_name(0)}")
        print(f"  VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
    
    # -------------------------------------------------------------------------
    # HYPERPARAMETERS
    # -------------------------------------------------------------------------
    
    EPOCHS = 20
    BATCH_SIZE = 2
    LEARNING_RATE = 1e-5
    CROP_SIZE = 256
    NUM_WORKERS = 2
    
    print(f"\n{'='*70}")
    print("Training Configuration")
    print(f"{'='*70}")
    print(f"Epochs: {EPOCHS}")
    print(f"Batch Size: {BATCH_SIZE}")
    print(f"Learning Rate: {LEARNING_RATE}")
    print(f"Crop Size: {CROP_SIZE}×{CROP_SIZE}")
    print(f"Optimizer: Adam")
    print(f"Loss: L1Loss")
    print(f"{'='*70}\n")
    
    # -------------------------------------------------------------------------
    # DATASET & DATALOADER
    # -------------------------------------------------------------------------
    
    print("Loading dataset...")
    train_dataset = WagonDataset(root_dir='train/train', crop_size=CROP_SIZE)
    
    train_loader = DataLoader(
        train_dataset,
        batch_size=BATCH_SIZE,
        shuffle=True,
        num_workers=NUM_WORKERS,
        pin_memory=True
    )
    
    print(f"✓ Training batches per epoch: {len(train_loader)}\n")
    
    # -------------------------------------------------------------------------
    # MODEL SETUP
    # -------------------------------------------------------------------------
    
    print("Initializing model...")
    model = MIMOUNetPlus(num_res=20)
    model = model.to(device)
    
    # Load pre-trained weights from GoPro
    pretrained_path = 'weights/gopro_pretrained.pth'
    
    if os.path.exists(pretrained_path):
        print(f"✓ Loading pre-trained weights from: {pretrained_path}")
        
        # Load checkpoint
        checkpoint = torch.load(pretrained_path, map_location=device)
        
        # Handle different checkpoint formats
        if isinstance(checkpoint, dict):
            if 'model_state_dict' in checkpoint:
                model.load_state_dict(checkpoint['model_state_dict'])
            elif 'state_dict' in checkpoint:
                model.load_state_dict(checkpoint['state_dict'])
            else:
                model.load_state_dict(checkpoint)
        else:
            model.load_state_dict(checkpoint)
        
        print("✓ Pre-trained weights loaded successfully")
        print("  Strategy: Fine-tuning (all layers trainable)\n")
    else:
        print(f"⚠ Pre-trained weights not found at: {pretrained_path}")
        print("  Training from scratch (not recommended)\n")
    
    # -------------------------------------------------------------------------
    # LOSS & OPTIMIZER
    # -------------------------------------------------------------------------
    
    criterion = nn.L1Loss()
    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)
    
    # -------------------------------------------------------------------------
    # CREATE WEIGHTS DIRECTORY
    # -------------------------------------------------------------------------
    
    os.makedirs('weights', exist_ok=True)
    
    # -------------------------------------------------------------------------
    # TRAINING LOOP
    # -------------------------------------------------------------------------
    
    print("="*70)
    print("Starting Training")
    print("="*70 + "\n")
    
    best_loss = float('inf')
    
    for epoch in range(1, EPOCHS + 1):
        print(f"\n{'='*70}")
        print(f"Epoch {epoch}/{EPOCHS}")
        print(f"{'='*70}")
        
        # Train
        train_loss = train_epoch(model, train_loader, criterion, optimizer, device, epoch)
        
        print(f"\n✓ Epoch {epoch} Complete")
        print(f"  Average Training Loss: {train_loss:.4f}")
        
        # Save checkpoint at epochs 10 and 20
        if epoch in [10, 20]:
            checkpoint_path = f'weights/wagon_epoch_{epoch}.pth'
            torch.save({
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'loss': train_loss,
            }, checkpoint_path)
            print(f"  ✓ Saved checkpoint: {checkpoint_path}")
        
        # Save best model
        if train_loss < best_loss:
            best_loss = train_loss
            best_path = 'weights/wagon_best.pth'
            torch.save({
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'loss': train_loss,
            }, best_path)
            print(f"  ✓ New best model saved: {best_path} (Loss: {best_loss:.4f})")
    
    print("\n" + "="*70)
    print("Training Complete!")
    print("="*70)
    print(f"Best Loss: {best_loss:.4f}")
    print(f"Saved Models:")
    print(f"  - weights/wagon_epoch_10.pth")
    print(f"  - weights/wagon_epoch_20.pth")
    print(f"  - weights/wagon_best.pth")
    print("="*70 + "\n")


if __name__ == '__main__':
    main()
