# 🎯 COMPLETE FINE-TUNING SOLUTION

## ✅ WHAT'S BEEN DONE

I've modified your project to fine-tune MIMO-UNetPlus **exclusively** on your wagon dataset.

### Modified Files:
1. ✅ **train.py** - Complete rewrite for wagon fine-tuning
2. ✅ **WAGON_FINETUNING_GUIDE.md** - Comprehensive guide
3. ✅ **WAGON_QUICK_START.md** - Quick reference
4. ✅ **setup_pretrained.py** - Helper to prepare weights

---

## 🚀 HOW TO START (3 STEPS)

### Step 1: Setup Pretrained Weights
```powershell
python setup_pretrained.py
```
This will:
- Search for available pretrained weights
- Copy `gopro_best.pth` → `gopro_pretrained.pth`
- Confirm you're ready to train

### Step 2: Start Training
```powershell
python train.py
```
This will:
- Load wagon dataset from `train/train/blur/` and `train/train/sharp/`
- Fine-tune from pretrained weights
- Train for 20 epochs
- Save checkpoints automatically

### Step 3: Monitor GPU
In a separate PowerShell window:
```powershell
nvidia-smi -l 1
```
You should see:
- GPU utilization: 80-100%
- Memory usage: ~4-5 GB / 6 GB

---

## 📋 EXACT COMMAND SEQUENCE

```powershell
# 1. Activate virtual environment (if not already active)
& C:\Users\Soham\OneDrive\Desktop\blur\venv\Scripts\Activate.ps1

# 2. Setup pretrained weights (one-time setup)
python setup_pretrained.py

# 3. Start training
python train.py

# 4. (Optional) Monitor GPU in new window
nvidia-smi -l 1
```

---

## 🎛️ CONFIGURATION DETAILS

### Dataset
- **Source**: `train/train/blur/` and `train/train/sharp/`
- **Pairing**: Matches images by filename
- **Preprocessing**: Random crop to 256×256

### Model
- **Architecture**: MIMOUNetPlus (from `models/mimo_official.py`)
- **Initial Weights**: `weights/gopro_pretrained.pth`
- **Strategy**: Fine-tuning (all layers trainable)

### Training Parameters
```python
EPOCHS = 20              # Fast convergence for fine-tuning
BATCH_SIZE = 2           # Safe for 6GB VRAM
LEARNING_RATE = 1e-5     # Low LR preserves pretrained features
CROP_SIZE = 256          # Standard size for deblurring
NUM_WORKERS = 2          # Parallel data loading
```

### Loss & Optimization
- **Loss**: L1Loss (Mean Absolute Error)
- **Optimizer**: Adam
- **Multi-scale**: Uses 3 outputs from MIMO-UNet
- **No LR scheduler**: Constant 1e-5

### Checkpointing
Automatically saves:
- `weights/wagon_epoch_10.pth` (at epoch 10)
- `weights/wagon_epoch_20.pth` (at epoch 20)
- `weights/wagon_best.pth` (whenever loss improves)

---

## ⏱️ EXPECTED TIMELINE

Assuming ~50 wagon image pairs:

| Metric | Value |
|--------|-------|
| Batches per epoch | 25 (50 images ÷ 2 batch size) |
| Seconds per batch | 5-10 seconds |
| Minutes per epoch | 2-4 minutes |
| **Total time (20 epochs)** | **40-80 minutes** |

Progress printed every 10 batches.

---

## 📊 TRAINING OUTPUT EXAMPLE

```
======================================================================
MIMO-UNetPlus Fine-Tuning on Wagon Dataset
======================================================================

✓ Device: cuda
  GPU: NVIDIA GeForce RTX 3050 Laptop GPU
  VRAM: 6.00 GB

======================================================================
Training Configuration
======================================================================
Epochs: 20
Batch Size: 2
Learning Rate: 1e-05
Crop Size: 256×256
Optimizer: Adam
Loss: L1Loss
======================================================================

Loading dataset...

======================================================================
Loading wagon dataset from: train/train
======================================================================
Blur images found: 50
✓ Valid image pairs: 50
======================================================================

✓ Training batches per epoch: 25

Initializing model...
✓ Loading pre-trained weights from: weights/gopro_pretrained.pth
✓ Pre-trained weights loaded successfully
  Strategy: Fine-tuning (all layers trainable)

======================================================================
Starting Training
======================================================================

======================================================================
Epoch 1/20
======================================================================
  Batch [10/25] | Loss: 0.0234
  Batch [20/25] | Loss: 0.0198
  Batch [25/25] | Loss: 0.0212

✓ Epoch 1 Complete
  Average Training Loss: 0.0218

...

======================================================================
Epoch 10/20
======================================================================
  Batch [10/25] | Loss: 0.0089
  Batch [20/25] | Loss: 0.0076
  Batch [25/25] | Loss: 0.0081

✓ Epoch 10 Complete
  Average Training Loss: 0.0083
  ✓ Saved checkpoint: weights/wagon_epoch_10.pth
  ✓ New best model saved: weights/wagon_best.pth (Loss: 0.0083)

...

======================================================================
Training Complete!
======================================================================
Best Loss: 0.0061
Saved Models:
  - weights/wagon_epoch_10.pth
  - weights/wagon_epoch_20.pth
  - weights/wagon_best.pth
======================================================================
```

---

## 🧪 WHY FINE-TUNING? (Technical Explanation)

### The Problem with Training from Scratch

When training on a **small dataset** (50 wagon images) from random initialization:

❌ **Overfitting**: Model memorizes training data  
❌ **Poor generalization**: Fails on new wagons  
❌ **Slow convergence**: Needs 100+ epochs  
❌ **Unstable training**: Loss fluctuates wildly  

### The Solution: Transfer Learning via Fine-Tuning

**Pre-trained GoPro Model Knows**:
- Generic blur patterns (motion, defocus, camera shake)
- Edge detection and reconstruction
- Multi-scale feature extraction
- Texture synthesis

**Fine-tuning Adapts to**:
- Wagon-specific shapes and structures
- Your camera's blur characteristics
- Your lighting conditions
- Domain-specific patterns

### Mathematical Intuition

**From Scratch**:
```
θ_final = θ_random + Σ(gradients from 50 wagon images)
         └─ Random noise     └─ Weak signal
```

**Fine-Tuning**:
```
θ_final = θ_gopro + Σ(small adjustments from wagon images)
         └─ Rich features    └─ Targeted refinement
```

### Why Learning Rate = 1e-5?

**High LR (2e-4)**: Used for training from scratch
- Large weight updates
- Explores parameter space broadly
- Risk: Catastrophic forgetting of GoPro features

**Low LR (1e-5)**: Used for fine-tuning
- Small, gentle adjustments
- Preserves pre-learned features
- Adapts gradually to new domain

**Analogy**: 
- High LR = Demolishing and rebuilding a house
- Low LR = Redecorating existing rooms

---

## 🔧 IMPLEMENTATION DETAILS

### WagonDataset Class
```python
class WagonDataset(Dataset):
    def __init__(self, root_dir='train/train', crop_size=256):
        # Scans train/train/blur/ for all images
        # Matches with train/train/sharp/ by filename
        # Handles any image format (.png, .jpg, etc.)
```

**Key Features**:
- ✅ Automatic filename matching
- ✅ Auto-resize if images < 256×256
- ✅ Random crop augmentation
- ✅ BGR→RGB conversion
- ✅ Normalization to [0, 1]

### Multi-Scale Loss
```python
# MIMO-UNetPlus outputs 3 scales
if isinstance(outputs, list):
    loss = sum([criterion(out, sharp) for out in outputs])
```

**Benefits**:
- Better detail preservation
- Faster convergence
- Multi-resolution supervision

### Checkpoint Strategy
```python
# Save at specific epochs
if epoch in [10, 20]:
    save_checkpoint()

# Save when loss improves
if train_loss < best_loss:
    save_best_model()
```

**Result**: Always have the best model saved

---

## 🛠️ TROUBLESHOOTING

### Issue: "RuntimeError: CUDA out of memory"

**Cause**: 6GB VRAM is tight

**Solutions** (try in order):
1. Reduce batch size to 1:
   ```python
   # Line 220 in train.py
   BATCH_SIZE = 1
   ```

2. Reduce crop size to 128:
   ```python
   # Line 222 in train.py
   CROP_SIZE = 128
   ```

3. Close other GPU programs (Chrome, games, etc.)

4. Enable gradient checkpointing (advanced)

### Issue: "No valid image pairs found"

**Cause**: Dataset structure mismatch

**Check**:
```
train/
└── train/
    ├── blur/
    │   ├── wagon001.jpg
    │   └── wagon002.jpg
    └── sharp/
        ├── wagon001.jpg  ← Must match blur filenames
        └── wagon002.jpg
```

**Fix**: Rename files to match exactly

### Issue: "Pre-trained weights not found"

**Cause**: `gopro_pretrained.pth` missing

**Fix**:
```powershell
python setup_pretrained.py
```
This will help you select and prepare weights.

**Manual fix**:
```powershell
Copy-Item weights/gopro_best.pth weights/gopro_pretrained.pth
```

### Issue: Training is very slow

**Possible causes**:

1. **CPU mode** (not using GPU)
   - Check output for `Device: cuda`
   - Run `nvidia-smi` to verify GPU detected

2. **NUM_WORKERS bottleneck**
   ```python
   # Line 223 in train.py - try reducing to 0
   NUM_WORKERS = 0
   ```

3. **Large images** (>4K resolution)
   - Will auto-crop but loading is slow
   - Consider pre-resizing dataset

### Issue: Loss not decreasing

**Possible causes**:

1. **Learning rate too low**
   - Try 5e-5 instead of 1e-5
   - Edit line 221 in train.py

2. **Bad pretrained weights**
   - Try different checkpoint

3. **Dataset quality issues**
   - Check blur/sharp pairs are correct
   - Verify images aren't corrupted

---

## 📈 AFTER TRAINING: USING YOUR MODEL

### Option 1: Use Existing Inference Scripts

Check these files in your project:
- `run_deblur.py`
- `browse_and_deblur.py`
- `safe_inference.py`

Modify to use `weights/wagon_best.pth`

### Option 2: Quick Test Script

Create `test_wagon_inference.py`:

```python
import torch
import cv2
import numpy as np
from models.mimo_official import MIMOUNetPlus

# Setup
device = torch.device('cuda')
model = MIMOUNetPlus(num_res=20).to(device)

# Load fine-tuned weights
checkpoint = torch.load('weights/wagon_best.pth', map_location=device)
model.load_state_dict(checkpoint['model_state_dict'])
model.eval()

# Load test image
img = cv2.imread('test_blur.jpg')
img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
img_norm = img_rgb.astype(np.float32) / 255.0

# To tensor [1, 3, H, W]
img_tensor = torch.from_numpy(img_norm.transpose(2, 0, 1)).unsqueeze(0).to(device)

# Inference
with torch.no_grad():
    output = model(img_tensor)
    if isinstance(output, list):
        output = output[-1]  # Use final scale

# Post-process
result = output[0].cpu().numpy().transpose(1, 2, 0)
result = (result * 255).clip(0, 255).astype(np.uint8)
result_bgr = cv2.cvtColor(result, cv2.COLOR_RGB2BGR)

# Save
cv2.imwrite('test_sharp.jpg', result_bgr)
print("✓ Saved deblurred image!")
```

Run:
```powershell
python test_wagon_inference.py
```

---

## 📚 ADDITIONAL RESOURCES

### Project Files
- 📄 `train.py` - Main training script
- 📄 `WAGON_FINETUNING_GUIDE.md` - Full documentation
- 📄 `WAGON_QUICK_START.md` - Quick reference
- 📄 `setup_pretrained.py` - Weights setup helper

### Model Information
- 📁 `models/mimo_official.py` - Model architecture
- 📁 `weights/` - Checkpoints directory

### Existing Inference Scripts
- 📄 `run_deblur.py` - Basic deblurring
- 📄 `browse_and_deblur.py` - Batch processing
- 📄 `safe_inference.py` - Safe inference wrapper

---

## 🎯 SUMMARY CHECKLIST

Before training:
- [ ] Virtual environment activated
- [ ] Wagon dataset in `train/train/blur/` and `train/train/sharp/`
- [ ] Filenames match between blur and sharp folders
- [ ] Run `python setup_pretrained.py` to prepare weights

Start training:
- [ ] Run `python train.py`
- [ ] Verify GPU usage with `nvidia-smi -l 1`
- [ ] Watch for checkpoint saves at epochs 10, 20

After training:
- [ ] Best model saved to `weights/wagon_best.pth`
- [ ] Test on new wagon images
- [ ] Compare with original pretrained model

---

## 🚀 READY TO GO!

Everything is set up. Just run:

```powershell
python setup_pretrained.py  # One-time setup
python train.py             # Start training
```

Good luck with your wagon deblurring project! 🚂✨

---

## 💡 PRO TIPS

1. **Save your original pretrained weights**
   ```powershell
   Copy-Item weights/gopro_pretrained.pth weights/gopro_pretrained_backup.pth
   ```

2. **Monitor loss trends**
   - Should decrease gradually
   - If flat after 5 epochs, increase LR slightly

3. **Experiment after first run**
   - Try LR = 5e-5 or 2e-5
   - Try different crop sizes (128, 192, 256)
   - Try batch size 4 if you have more VRAM

4. **Data quality matters more than quantity**
   - 50 high-quality pairs > 200 low-quality pairs
   - Ensure sharp images are truly sharp
   - Ensure blur types match your test cases

5. **Compare models**
   - Test epoch_10 vs epoch_20 vs best
   - Sometimes earlier checkpoints generalize better

---

**Questions?** Check `WAGON_FINETUNING_GUIDE.md` for more details.
