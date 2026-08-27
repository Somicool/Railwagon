"""
Improved fine-tuning with better hyperparameters
Based on analysis: 91.7% sharpness loss = severe blur = high potential
Target: 28-30 dB (vs current 25.4 dB)
"""
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
import torchvision.transforms as transforms
from pathlib import Path
import cv2
import numpy as np
from tqdm import tqdm
import sys
sys.path.append('models')
from mimo_unet_plus import MIMOUNetPlus

# Improved hyperparameters
EPOCHS = 50
BATCH_SIZE = 2  # Smaller for better gradient quality
LR = 2e-4  # Higher learning rate  
PATCH_SIZE = 384  # Larger patches for better context
WARMUP_EPOCHS = 3

class DeblurDatasetImproved(Dataset):
    def __init__(self, blur_dir, sharp_dir, patch_size=384, is_train=True):
        self.blur_paths = sorted(list(Path(blur_dir).glob('*.jpg')))
        self.sharp_paths = sorted(list(Path(sharp_dir).glob('*.jpg')))
        self.patch_size = patch_size
        self.is_train = is_train
        
        # Stronger augmentation
        if is_train:
            self.aug_prob = 0.7  # Increased from 0.5
        
    def __len__(self):
        return len(self.blur_paths)
    
    def augment(self, blur, sharp):
        """Stronger data augmentation"""
        # Random crop
        h, w = blur.shape[:2]
        if h > self.patch_size and w > self.patch_size:
            top = np.random.randint(0, h - self.patch_size)
            left = np.random.randint(0, w - self.patch_size)
            blur = blur[top:top+self.patch_size, left:left+self.patch_size]
            sharp = sharp[top:top+self.patch_size, left:left+self.patch_size]
        
        # Random flip
        if np.random.rand() < 0.5:
            blur = cv2.flip(blur, 1)
            sharp = cv2.flip(sharp, 1)
        if np.random.rand() < 0.5:
            blur = cv2.flip(blur, 0)
            sharp = cv2.flip(sharp, 0)
        
        # Random rotation (90, 180, 270)
        if np.random.rand() < 0.75:
            k = np.random.randint(1, 4)
            blur = np.rot90(blur, k).copy()
            sharp = np.rot90(sharp, k).copy()
        
        # Color jitter (helps robustness)
        if np.random.rand() < self.aug_prob:
            # Brightness
            factor = 1.0 + (np.random.rand() - 0.5) * 0.3
            blur = np.clip(blur * factor, 0, 255).astype(np.uint8)
            sharp = np.clip(sharp * factor, 0, 255).astype(np.uint8)
        
        if np.random.rand() < self.aug_prob:
            # Contrast
            factor = 1.0 + (np.random.rand() - 0.5) * 0.3
            mean_b = blur.mean()
            mean_s = sharp.mean()
            blur = np.clip((blur - mean_b) * factor + mean_b, 0, 255).astype(np.uint8)
            sharp = np.clip((sharp - mean_s) * factor + mean_s, 0, 255).astype(np.uint8)
        
        return blur, sharp
    
    def __getitem__(self, idx):
        blur_img = cv2.imread(str(self.blur_paths[idx]))
        sharp_img = cv2.imread(str(self.sharp_paths[idx]))
        
        if self.is_train:
            blur_img, sharp_img = self.augment(blur_img, sharp_img)
        
        # Pad to patch_size if needed
        h, w = blur_img.shape[:2]
        if h < self.patch_size or w < self.patch_size:
            pad_h = max(0, self.patch_size - h)
            pad_w = max(0, self.patch_size - w)
            blur_img = cv2.copyMakeBorder(blur_img, 0, pad_h, 0, pad_w, cv2.BORDER_REFLECT)
            sharp_img = cv2.copyMakeBorder(sharp_img, 0, pad_h, 0, pad_w, cv2.BORDER_REFLECT)
        
        # Convert to tensor
        blur_tensor = torch.from_numpy(blur_img).permute(2, 0, 1).float() / 255.0
        sharp_tensor = torch.from_numpy(sharp_img).permute(2, 0, 1).float() / 255.0
        
        return blur_tensor, sharp_tensor

class PSNRLoss(nn.Module):
    def __init__(self, max_val=1.0):
        super().__init__()
        self.max_val = max_val
        self.mse = nn.MSELoss()
    
    def forward(self, pred, target):
        mse = self.mse(pred, target)
        return -10 * torch.log10(mse / (self.max_val ** 2))

def main():
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Device: {device}")
    print(f"\nImproved Training Configuration:")
    print(f"  Epochs: {EPOCHS}")
    print(f"  Batch Size: {BATCH_SIZE}")
    print(f"  Learning Rate: {LR}")
    print(f"  Patch Size: {PATCH_SIZE}")
    print(f"  Warmup Epochs: {WARMUP_EPOCHS}")
    print()
    
    # Load data
    train_dataset = DeblurDatasetImproved('train/train/blur', 'train/train/sharp', 
                                           patch_size=PATCH_SIZE, is_train=True)
    # Split train/val
    train_size = int(0.9 * len(train_dataset))
    val_size = len(train_dataset) - train_size
    train_set, val_set = torch.utils.data.random_split(train_dataset, [train_size, val_size])
    
    train_loader = DataLoader(train_set, batch_size=BATCH_SIZE, shuffle=True, num_workers=2)
    val_loader = DataLoader(val_set, batch_size=1, shuffle=False)
    
    print(f"Training samples: {len(train_set)}")
    print(f"Validation samples: {len(val_set)}\n")
    
    # Model
    model = MIMOUNetPlus().to(device)
    
    # Load previous best if exists and continue training
    start_epoch = 0
    best_psnr = 0
    if Path('checkpoints/best_model.pkl').exists():
        print("Loading previous best model to continue training...")
        checkpoint = torch.load('checkpoints/best_model.pkl')
        model.load_state_dict(checkpoint)
        print("✓ Loaded\n")
    
    # Loss and optimizer
    criterion = nn.L1Loss()  # Charbonnier approximated as L1
    optimizer = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=1e-4)
    
    # Learning rate scheduler with warmup
    def lr_lambda(epoch):
        if epoch < WARMUP_EPOCHS:
            return (epoch + 1) / WARMUP_EPOCHS
        else:
            return 0.5 * (1 + np.cos(np.pi * (epoch - WARMUP_EPOCHS) / (EPOCHS - WARMUP_EPOCHS)))
    
    scheduler = torch.optim.lr_scheduler.LambdaLR(optimizer, lr_lambda)
    
    # Training loop
    for epoch in range(start_epoch, EPOCHS):
        model.train()
        train_loss = 0
        train_psnr = 0
        
        pbar = tqdm(train_loader, desc=f"Epoch {epoch+1}/{EPOCHS}")
        for blur, sharp in pbar:
            blur, sharp = blur.to(device), sharp.to(device)
            
            optimizer.zero_grad()
            
            output = model(blur)
            if isinstance(output, (list, tuple)):
                output = output[0]
            
            loss = criterion(output, sharp)
            loss.backward()
            
            # Gradient clipping for stability
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            
            optimizer.step()
            
            # Calculate PSNR
            with torch.no_grad():
                mse = ((output - sharp) ** 2).mean()
                psnr = -10 * torch.log10(mse)
            
            train_loss += loss.item()
            train_psnr += psnr.item()
            
            pbar.set_postfix({'loss': f'{loss.item():.4f}', 'psnr': f'{psnr.item():.2f}'})
        
        train_loss /= len(train_loader)
        train_psnr /= len(train_loader)
        
        # Validation
        model.eval()
        val_psnr = 0
        with torch.no_grad():
            for blur, sharp in val_loader:
                blur, sharp = blur.to(device), sharp.to(device)
                
                output = model(blur)
                if isinstance(output, (list, tuple)):
                    output = output[0]
                
                mse = ((output - sharp) ** 2).mean()
                psnr = -10 * torch.log10(mse)
                val_psnr += psnr.item()
        
        val_psnr /= len(val_loader)
        
        print(f"Epoch {epoch+1}: Train Loss={train_loss:.4f}, Train PSNR={train_psnr:.2f} dB, Val PSNR={val_psnr:.2f} dB, LR={scheduler.get_last_lr()[0]:.2e}")
        
        # Save best model
        if val_psnr > best_psnr:
            best_psnr = val_psnr
            torch.save(model.state_dict(), 'checkpoints/best_model_improved.pkl')
            print(f"  ★ New best model saved! ({val_psnr:.2f} dB)")
        
        scheduler.step()
        
        # Save checkpoint every 10 epochs
        if (epoch + 1) % 10 == 0:
            torch.save(model.state_dict(), f'checkpoints/checkpoint_epoch{epoch+1}_improved.pkl')
    
    print(f"\n{'='*70}")
    print(f"Training Complete!")
    print(f"Best Validation PSNR: {best_psnr:.2f} dB")
    print(f"Previous best was: 25.30 dB")
    print(f"Improvement: {best_psnr - 25.30:+.2f} dB")
    print(f"{'='*70}")

if __name__ == '__main__':
    main()
