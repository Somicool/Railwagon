# MIMO-UNetPlus Fine-Tuning Guide for Wagon Dataset

## Overview
This guide explains how to fine-tune a pre-trained MIMO-UNetPlus model on your custom wagon dataset.

---

## ✅ What Has Been Done

### Modified `train.py`
The training script has been completely rewritten to:
- Use **WagonDataset** class for your `train/blur` and `train/sharp` folders
- Load pre-trained weights from `weights/gopro_pretrained.pth`
- Fine-tune (NOT train from scratch)
- Use all your specified hyperparameters
- Save checkpoints at epochs 10, 20, and best model

---

## 🚀 How to Start Training

### Step 1: Activate Virtual Environment
```powershell
& C:\Users\Soham\OneDrive\Desktop\blur\venv\Scripts\Activate.ps1
```

### Step 2: Start Training
```powershell
python train.py
```

That's it! The training will start automatically.

---

## 📊 What You'll See

### During Training:
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

======================================================================
Epoch 1/20
======================================================================
  Batch [10/25] | Loss: 0.0234
  Batch [20/25] | Loss: 0.0198
  Batch [25/25] | Loss: 0.0212

✓ Epoch 1 Complete
  Average Training Loss: 0.0218
```

### Progress Indicators:
- ✓ Batch progress every 10 batches
- ✓ Loss value for each batch
- ✓ Average loss per epoch
- ✓ Checkpoint saves at epochs 10, 20
- ✓ Best model saves when loss improves

---

## 💾 Output Files

### After Training Completes:

```
weights/
├── wagon_epoch_10.pth     ← Checkpoint at epoch 10
├── wagon_epoch_20.pth     ← Final checkpoint
└── wagon_best.pth         ← Best model (lowest loss)
```

**Use `wagon_best.pth` for inference on new images.**

---

## 🔍 How to Verify GPU Usage

### Method 1: Check Training Output
Look for this line at the start:
```
✓ Device: cuda
  GPU: NVIDIA GeForce RTX 3050 Laptop GPU
```

If you see `Device: cpu`, GPU is NOT being used.

### Method 2: Monitor GPU in Real-Time

Open a **new PowerShell window** and run:
```powershell
nvidia-smi -l 1
```

This updates every 1 second. You should see:
- **GPU utilization**: 80-100%
- **Memory usage**: ~4-5 GB / 6 GB
- **Python process** using GPU

Press `Ctrl+C` to stop monitoring.

### Method 3: Task Manager
1. Open Task Manager (`Ctrl + Shift + Esc`)
2. Go to **Performance** tab
3. Select **GPU 0**
4. Watch "3D" and "Copy" graphs spike during training

---

## 📚 Why Fine-Tuning?

### Fine-Tuning vs Training from Scratch

| Aspect | Fine-Tuning | From Scratch |
|--------|-------------|--------------|
| **Starting Point** | Pre-trained on GoPro (large dataset) | Random weights |
| **Training Time** | **Fast** (20 epochs) | Slow (100+ epochs) |
| **Data Required** | **Small** (50-100 images) | Large (1000+ images) |
| **Quality** | **Better** (leverages learned features) | Worse (limited data) |
| **Risk of Overfitting** | **Lower** | Higher |

### Why Fine-Tuning for Your Wagon Dataset:

1. **Pre-learned Features**: The GoPro model already knows how to:
   - Detect blur patterns
   - Reconstruct sharp edges
   - Handle motion blur

2. **Domain Adaptation**: Fine-tuning adapts these features to:
   - Your specific wagon shapes
   - Your camera characteristics
   - Your blur types

3. **Efficiency**: 
   - Converges in 20 epochs instead of 100+
   - Works with small datasets (50 images vs 1000+)
   - Lower risk of overfitting

4. **Lower Learning Rate** (1e-5):
   - Gently adjusts pre-trained weights
   - Preserves learned general features
   - Prevents catastrophic forgetting

**Analogy**: Like a chef who knows cooking basics (GoPro) learning a new cuisine (wagon) vs. a beginner learning everything from scratch.

---

## ⚙️ Training Configuration Details

### Hyperparameters Used:
```python
EPOCHS = 20                # Fine-tuning converges faster
BATCH_SIZE = 2             # Fits in 6 GB VRAM
LEARNING_RATE = 1e-5       # Small LR for fine-tuning
CROP_SIZE = 256            # Random 256×256 crops
NUM_WORKERS = 2            # Parallel data loading
```

### Data Augmentation:
- **Random cropping**: 256×256 from larger images
- **Shuffling**: Random order each epoch
- **Automatic resizing**: If images < 256×256

### Loss Function:
- **L1Loss** (Mean Absolute Error)
- Multi-scale supervision (3 outputs)
- Better for preserving sharp edges

### Optimizer:
- **Adam** with default betas (0.9, 0.999)
- Adaptive learning rates per parameter
- No learning rate scheduler (constant 1e-5)

---

## 🛠️ Troubleshooting

### Problem: "No valid image pairs found"
**Solution**: Check that:
```
train/train/blur/image1.png
train/train/sharp/image1.png
```
Both have **identical filenames**.

### Problem: "CUDA out of memory"
**Solutions**:
1. Reduce `BATCH_SIZE` from 2 to 1 in `train.py` (line 190)
2. Reduce `CROP_SIZE` from 256 to 128 (line 192)
3. Close other GPU programs

### Problem: "Pre-trained weights not found"
**Solution**: Make sure you have:
```
weights/gopro_pretrained.pth
```
If missing, you can:
- Use `gopro_best.pth` instead (rename to `gopro_pretrained.pth`)
- Or train from scratch (slower, less optimal)

### Problem: Training is slow
**Possible causes**:
1. GPU not detected → Check with `nvidia-smi`
2. NUM_WORKERS too high → Reduce to 0 in `train.py` (line 193)
3. Images very large → Will be auto-cropped

---

## 📈 Expected Training Time

- **Per epoch**: ~2-5 minutes (depends on image count)
- **Total (20 epochs)**: ~40-100 minutes

With 50 image pairs:
- Batches per epoch = 50 / 2 = 25
- Time per batch ≈ 5-10 seconds
- Epoch time ≈ 2-4 minutes
- **Total ≈ 40-80 minutes**

---

## 🎯 After Training

### Use Your Fine-Tuned Model:

Create `test_wagon.py`:
```python
import torch
import cv2
from models.mimo_official import MIMOUNetPlus

# Load model
model = MIMOUNetPlus(num_res=20)
checkpoint = torch.load('weights/wagon_best.pth', map_location='cuda')
model.load_state_dict(checkpoint['model_state_dict'])
model = model.cuda()
model.eval()

# Load and preprocess image
img = cv2.imread('test_wagon_blur.jpg')
img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
img = img.astype('float32') / 255.0
img_tensor = torch.from_numpy(img.transpose(2, 0, 1)).unsqueeze(0).cuda()

# Deblur
with torch.no_grad():
    output = model(img_tensor)
    if isinstance(output, list):
        output = output[-1]  # Use finest scale

# Save result
result = output[0].cpu().numpy().transpose(1, 2, 0)
result = (result * 255).clip(0, 255).astype('uint8')
result = cv2.cvtColor(result, cv2.COLOR_RGB2BGR)
cv2.imwrite('test_wagon_sharp.jpg', result)
print("✓ Deblurred image saved!")
```

Run with:
```powershell
python test_wagon.py
```

---

## 📝 Summary

1. ✅ **Modified Script**: `train.py` now trains only on wagon dataset
2. ✅ **Command**: `python train.py`
3. ✅ **GPU Check**: `nvidia-smi -l 1`
4. ✅ **Output**: `weights/wagon_best.pth`
5. ✅ **Strategy**: Fine-tuning from GoPro weights
6. ✅ **Time**: ~40-80 minutes for 20 epochs

**You're ready to train!** Just run:
```powershell
python train.py
```

---

## 🔗 Related Files

- **Training Script**: `train.py`
- **Model Definition**: `models/mimo_official.py`
- **Pretrained Weights**: `weights/gopro_pretrained.pth`
- **Dataset**: `train/train/blur/` and `train/train/sharp/`

Good luck with your wagon deblurring project! 🚂✨
