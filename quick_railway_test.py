"""
Quick test: Compare old vs improved model on railway video frame
"""
import torch
import cv2
import numpy as np
from pathlib import Path
import sys
sys.path.append('models')
from mimo_unet_plus import MIMOUNetPlus

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# Load both models
print("Loading models...")
old_model = MIMOUNetPlus().to(device)
new_model = MIMOUNetPlus().to(device)

old_model.load_state_dict(torch.load('checkpoints/best_model.pkl'))
new_model.load_state_dict(torch.load('checkpoints/best_model_improved.pkl'))

old_model.eval()
new_model.eval()
print("✓ Loaded\n")

# Find a test image
test_frames = list(Path('train/train/blur').glob('*.jpg'))
img_path = test_frames[0]
print(f"Testing on: {img_path}\n")

# Load image
img = cv2.imread(str(img_path))
h, w = img.shape[:2]

# Pad to multiple of 16
pad_h = (16 - h % 16) % 16
pad_w = (16 - w % 16) % 16
img_padded = cv2.copyMakeBorder(img, 0, pad_h, 0, pad_w, cv2.BORDER_REFLECT)

# To tensor
img_tensor = torch.from_numpy(img_padded).permute(2, 0, 1).float() / 255.0
img_tensor = img_tensor.unsqueeze(0).to(device)

# Deblur with both models
print("Deblurring...")
with torch.no_grad():
    old_out = old_model(img_tensor)
    new_out = new_model(img_tensor)
    
    if isinstance(old_out, (list, tuple)):
        old_out = old_out[0]
    if isinstance(new_out, (list, tuple)):
        new_out = new_out[0]

# To numpy
old_result = old_out.squeeze(0).permute(1, 2, 0).cpu().numpy()
new_result = new_out.squeeze(0).permute(1, 2, 0).cpu().numpy()

old_result = np.clip(old_result * 255, 0, 255).astype(np.uint8)[:h, :w]
new_result = np.clip(new_result * 255, 0, 255).astype(np.uint8)[:h, :w]

# Create comparison
comparison = np.vstack([
    np.hstack([img, old_result]),
    np.hstack([new_result, np.zeros_like(img)])  # Leave space for text
])

# Add labels
cv2.putText(comparison, "Original (Blurry)", (10, 30), 
            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
cv2.putText(comparison, "Old Model (25.30 dB)", (w + 10, 30), 
            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
cv2.putText(comparison, "New Model (29.86 dB)", (10, h + 30), 
            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

cv2.imwrite('railway_comparison_old_vs_new.jpg', comparison)
print("✓ Saved: railway_comparison_old_vs_new.jpg")
print("\nVisual comparison created!")
print("Check if the new model looks better visually.")
