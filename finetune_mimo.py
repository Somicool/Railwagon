"""
Fine-tune MIMOUNetPlus model on custom dataset
Supports multi-scale loss and validation
"""

import os
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
from PIL import Image
import numpy as np
from tqdm import tqdm
import argparse
from models.mimo_unet_plus import MIMOUNetPlus


class DeblurDataset(Dataset):
    """Dataset for paired blur/sharp images"""
    
    def __init__(self, blur_dir, sharp_dir, patch_size=256, augment=True):
        self.blur_dir = blur_dir
        self.sharp_dir = sharp_dir
        self.patch_size = patch_size
        self.augment = augment
        
        # Get image files
        self.blur_images = sorted([f for f in os.listdir(blur_dir) if f.endswith(('.jpg', '.png'))])
        self.sharp_images = sorted([f for f in os.listdir(sharp_dir) if f.endswith(('.jpg', '.png'))])
        
        # Ensure matching pairs
        assert len(self.blur_images) == len(self.sharp_images), \
            f"Mismatch: {len(self.blur_images)} blur vs {len(self.sharp_images)} sharp images"
        
        print(f"Loaded {len(self.blur_images)} image pairs")
        
    def __len__(self):
        return len(self.blur_images)
    
    def __getitem__(self, idx):
        # Load images
        blur_path = os.path.join(self.blur_dir, self.blur_images[idx])
        sharp_path = os.path.join(self.sharp_dir, self.sharp_images[idx])
        
        blur_img = Image.open(blur_path).convert('RGB')
        sharp_img = Image.open(sharp_path).convert('RGB')
        
        # Convert to numpy
        blur_np = np.array(blur_img)
        sharp_np = np.array(sharp_img)
        
        # Extract random patch
        h, w = blur_np.shape[:2]
        if h > self.patch_size and w > self.patch_size:
            top = np.random.randint(0, h - self.patch_size)
            left = np.random.randint(0, w - self.patch_size)
            blur_np = blur_np[top:top+self.patch_size, left:left+self.patch_size]
            sharp_np = sharp_np[top:top+self.patch_size, left:left+self.patch_size]
        else:
            # Resize if image is smaller than patch size
            blur_img = blur_img.resize((self.patch_size, self.patch_size))
            sharp_img = sharp_img.resize((self.patch_size, self.patch_size))
            blur_np = np.array(blur_img)
            sharp_np = np.array(sharp_img)
        
        # Data augmentation
        if self.augment:
            # Random horizontal flip
            if np.random.random() > 0.5:
                blur_np = np.fliplr(blur_np).copy()
                sharp_np = np.fliplr(sharp_np).copy()
            
            # Random vertical flip
            if np.random.random() > 0.5:
                blur_np = np.flipud(blur_np).copy()
                sharp_np = np.flipud(sharp_np).copy()
            
            # Random rotation (90, 180, 270)
            if np.random.random() > 0.5:
                k = np.random.randint(1, 4)
                blur_np = np.rot90(blur_np, k).copy()
                sharp_np = np.rot90(sharp_np, k).copy()
        
        # Convert to tensor [0, 1]
        blur_tensor = torch.from_numpy(blur_np).float().permute(2, 0, 1) / 255.0
        sharp_tensor = torch.from_numpy(sharp_np).float().permute(2, 0, 1) / 255.0
        
        return blur_tensor, sharp_tensor


class CharbonnierLoss(nn.Module):
    """Charbonnier Loss (L1 variant)"""
    
    def __init__(self, eps=1e-6):
        super(CharbonnierLoss, self).__init__()
        self.eps = eps
    
    def forward(self, pred, target):
        diff = pred - target
        loss = torch.sqrt(diff * diff + self.eps * self.eps)
        return torch.mean(loss)


class PSNRMetric:
    """Calculate PSNR"""
    
    @staticmethod
    def calculate(pred, target):
        mse = torch.mean((pred - target) ** 2)
        if mse == 0:
            return float('inf')
        psnr = 20 * torch.log10(1.0 / torch.sqrt(mse))
        return psnr.item()


def train_epoch(model, dataloader, criterion, optimizer, device, epoch):
    """Train for one epoch"""
    model.train()
    total_loss = 0
    total_psnr = 0
    
    pbar = tqdm(dataloader, desc=f'Epoch {epoch} [Train]')
    for blur, sharp in pbar:
        blur = blur.to(device)
        sharp = sharp.to(device)
        
        # Forward pass - model outputs 3 scales
        outputs = model(blur)
        
        # Multi-scale loss
        loss = 0
        weights = [1.0, 0.6, 0.4]  # Weights for each scale
        for i, (out, weight) in enumerate(zip(outputs, weights)):
            # Downsample target for smaller scales
            if i == 1:
                target = nn.functional.avg_pool2d(sharp, kernel_size=2)
            elif i == 2:
                target = nn.functional.avg_pool2d(sharp, kernel_size=4)
            else:
                target = sharp
            
            loss += weight * criterion(out, target)
        
        # Backward pass
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        
        # Calculate PSNR on full resolution output
        with torch.no_grad():
            psnr = PSNRMetric.calculate(outputs[0], sharp)
        
        total_loss += loss.item()
        total_psnr += psnr
        
        pbar.set_postfix({
            'loss': f'{loss.item():.4f}',
            'psnr': f'{psnr:.2f}'
        })
    
    avg_loss = total_loss / len(dataloader)
    avg_psnr = total_psnr / len(dataloader)
    
    return avg_loss, avg_psnr


def validate(model, dataloader, criterion, device, epoch):
    """Validate the model"""
    model.eval()
    total_loss = 0
    total_psnr = 0
    
    pbar = tqdm(dataloader, desc=f'Epoch {epoch} [Valid]')
    with torch.no_grad():
        for blur, sharp in pbar:
            blur = blur.to(device)
            sharp = sharp.to(device)
            
            # Forward pass
            outputs = model(blur)
            
            # Multi-scale loss
            loss = 0
            weights = [1.0, 0.6, 0.4]
            for i, (out, weight) in enumerate(zip(outputs, weights)):
                if i == 1:
                    target = nn.functional.avg_pool2d(sharp, kernel_size=2)
                elif i == 2:
                    target = nn.functional.avg_pool2d(sharp, kernel_size=4)
                else:
                    target = sharp
                
                loss += weight * criterion(out, target)
            
            # Calculate PSNR
            psnr = PSNRMetric.calculate(outputs[0], sharp)
            
            total_loss += loss.item()
            total_psnr += psnr
            
            pbar.set_postfix({
                'loss': f'{loss.item():.4f}',
                'psnr': f'{psnr:.2f}'
            })
    
    avg_loss = total_loss / len(dataloader)
    avg_psnr = total_psnr / len(dataloader)
    
    return avg_loss, avg_psnr


def main():
    parser = argparse.ArgumentParser(description='Fine-tune MIMOUNetPlus')
    parser.add_argument('--train_blur', type=str, default='train/train/blur',
                        help='Path to training blur images')
    parser.add_argument('--train_sharp', type=str, default='train/train/sharp',
                        help='Path to training sharp images')
    parser.add_argument('--val_split', type=float, default=0.1,
                        help='Validation split ratio (default: 0.1)')
    parser.add_argument('--batch_size', type=int, default=4,
                        help='Batch size (default: 4)')
    parser.add_argument('--patch_size', type=int, default=256,
                        help='Training patch size (default: 256)')
    parser.add_argument('--epochs', type=int, default=100,
                        help='Number of epochs (default: 100)')
    parser.add_argument('--lr', type=float, default=1e-4,
                        help='Learning rate (default: 1e-4)')
    parser.add_argument('--resume', type=str, default=None,
                        help='Path to checkpoint to resume from')
    parser.add_argument('--pretrained', type=str, default='weights/MIMO-UNetPlus.pkl',
                        help='Path to pretrained weights')
    parser.add_argument('--save_dir', type=str, default='checkpoints',
                        help='Directory to save checkpoints')
    parser.add_argument('--num_workers', type=int, default=4,
                        help='Number of data loading workers')
    
    args = parser.parse_args()
    
    # Create save directory
    os.makedirs(args.save_dir, exist_ok=True)
    
    # Device
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Using device: {device}")
    
    # Create full dataset
    full_dataset = DeblurDataset(
        blur_dir=args.train_blur,
        sharp_dir=args.train_sharp,
        patch_size=args.patch_size,
        augment=True
    )
    
    # Split into train and validation
    val_size = int(len(full_dataset) * args.val_split)
    train_size = len(full_dataset) - val_size
    
    train_dataset, val_dataset = torch.utils.data.random_split(
        full_dataset, [train_size, val_size]
    )
    
    print(f"Train samples: {len(train_dataset)}, Val samples: {len(val_dataset)}")
    
    # Create dataloaders
    train_loader = DataLoader(
        train_dataset,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=args.num_workers,
        pin_memory=True
    )
    
    val_loader = DataLoader(
        val_dataset,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=args.num_workers,
        pin_memory=True
    )
    
    # Create model
    model = MIMOUNetPlus(num_res=8).to(device)
    
    # Load pretrained weights if available
    start_epoch = 0
    best_psnr = 0
    
    if args.resume:
        print(f"Resuming from checkpoint: {args.resume}")
        checkpoint = torch.load(args.resume, map_location=device)
        model.load_state_dict(checkpoint['model_state_dict'])
        start_epoch = checkpoint['epoch'] + 1
        best_psnr = checkpoint.get('best_psnr', 0)
        print(f"Resumed from epoch {start_epoch}, best PSNR: {best_psnr:.2f}")
    elif args.pretrained and os.path.exists(args.pretrained):
        print(f"Loading pretrained weights: {args.pretrained}")
        state_dict = torch.load(args.pretrained, map_location=device)
        model.load_state_dict(state_dict, strict=False)
        print("Pretrained weights loaded successfully")
    else:
        print("Training from scratch")
    
    # Loss function
    criterion = CharbonnierLoss()
    
    # Optimizer
    optimizer = optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-4)
    
    # Learning rate scheduler
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs, eta_min=1e-6)
    
    # Training loop
    print("\nStarting training...")
    print(f"Total epochs: {args.epochs}, Starting from: {start_epoch}")
    
    for epoch in range(start_epoch, args.epochs):
        # Train
        train_loss, train_psnr = train_epoch(
            model, train_loader, criterion, optimizer, device, epoch + 1
        )
        
        # Validate
        val_loss, val_psnr = validate(
            model, val_loader, criterion, device, epoch + 1
        )
        
        # Update learning rate
        scheduler.step()
        
        # Print epoch summary
        print(f"\nEpoch {epoch + 1}/{args.epochs}")
        print(f"Train - Loss: {train_loss:.4f}, PSNR: {train_psnr:.2f} dB")
        print(f"Valid - Loss: {val_loss:.4f}, PSNR: {val_psnr:.2f} dB")
        print(f"LR: {optimizer.param_groups[0]['lr']:.6f}")
        
        # Save checkpoint
        checkpoint = {
            'epoch': epoch,
            'model_state_dict': model.state_dict(),
            'optimizer_state_dict': optimizer.state_dict(),
            'scheduler_state_dict': scheduler.state_dict(),
            'train_loss': train_loss,
            'val_loss': val_loss,
            'train_psnr': train_psnr,
            'val_psnr': val_psnr,
            'best_psnr': best_psnr
        }
        
        # Save latest checkpoint
        torch.save(checkpoint, os.path.join(args.save_dir, 'latest.pth'))
        
        # Save best checkpoint
        if val_psnr > best_psnr:
            best_psnr = val_psnr
            checkpoint['best_psnr'] = best_psnr
            torch.save(checkpoint, os.path.join(args.save_dir, 'best.pth'))
            torch.save(model.state_dict(), os.path.join(args.save_dir, 'best_model.pkl'))
            print(f"★ New best model saved! PSNR: {best_psnr:.2f} dB")
        
        # Save periodic checkpoint
        if (epoch + 1) % 10 == 0:
            torch.save(checkpoint, os.path.join(args.save_dir, f'epoch_{epoch+1}.pth'))
    
    print("\n✓ Training completed!")
    print(f"Best validation PSNR: {best_psnr:.2f} dB")
    print(f"Checkpoints saved in: {args.save_dir}")


if __name__ == '__main__':
    main()
