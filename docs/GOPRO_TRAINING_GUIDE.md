# MIMO-UNetPlus GoPro Training Guide

## ✅ Training Script Ready!

Your [train.py](train.py) is now configured for **full GoPro training from scratch** (70 epochs).

---

## 🚀 Start Training

### Windows PowerShell Command:
```powershell
# 1. Activate virtual environment
cd C:\Users\Soham\OneDrive\Desktop\blur
.\venv\Scripts\Activate.ps1

# 2. Start training
python train.py
```

**That's it!** Training will run for 70 epochs automatically.

---

## ⏱️ Training Time Estimate

- **Batches per epoch**: ~545 batches (2,185 images ÷ 4 batch size)
- **Time per batch**: ~0.8-1.5 seconds (RTX 3050)
- **Time per epoch**: ~7-14 minutes
- **Total training time**: **8-16 hours** (70 epochs)

💡 **Tip:** Start training before bed or when you won't need your computer!

---

## 🔍 Monitor GPU Usage During Training

### Option 1: Real-Time Monitoring
Open a **new PowerShell window** and run:
```powershell
nvidia-smi -l 1
```
Updates every 1 second.

### Option 2: Single Check
```powershell
nvidia-smi
```

### What to Look For:
- **GPU Utilization**: Should be 90-100%
- **Memory Usage**: ~4-5 GB / 6 GB (batch_size=4)
- **Temperature**: Should stay under 85°C
- **Power**: Near maximum (e.g., 60-75W)

### Interpreting nvidia-smi Output:
```
+-----------------------------------------------------------------------------+
| NVIDIA-SMI 536.xx       Driver Version: 536.xx       CUDA Version: 12.x   |
|-------------------------------+----------------------+----------------------+
| GPU  Name            TCC/WDDM | Bus-Id        Disp.A | Volatile Uncorr. ECC |
| Fan  Temp  Perf  Pwr:Usage/Cap|         Memory-Usage | GPU-Util  Compute M. |
|===============================+======================+======================|
|   0  NVIDIA GeForce ... WDDM  | 00000000:01:00.0 Off |                  N/A |
| N/A   72C    P0    65W /  75W |   4512MiB /  6144MiB |     98%      Default |
+-------------------------------+----------------------+----------------------+
```

**Key indicators:**
- `98%` GPU utilization = ✅ Training is using GPU
- `4512MiB / 6144MiB` = ✅ Using ~4.5GB memory
- `72C` temperature = ✅ Safe operating temp

---

## 📊 Expected Training Output

```
======================================================================
MIMO-UNETPLUS TRAINING ON GOPRO DATASET
Motion Deblurring from Scratch
======================================================================
Device: cuda
GPU: NVIDIA GeForce RTX 3050 Laptop GPU
GPU Memory: 6.00 GB
CUDA Version: 12.1
======================================================================

[1/5] Loading dataset...

======================================================================
Loading train dataset from: GOPRO_Large
======================================================================
✓ Loaded 2185 image pairs
======================================================================

✓ Dataset loaded successfully
  - Total training samples: 2185
  - Batch size: 4
  - Batches per epoch: 546
  - Random crop size: 256×256

[2/5] Creating model...
✓ Model created successfully
  - Architecture: MIMO-UNetPlus
  - Total parameters: 16,115,267
  - Trainable parameters: 16,115,267
  - Model location: cuda

[3/5] Setting up training components...
✓ Loss function: L1Loss
✓ Optimizer: Adam (lr=0.0002, betas=(0.9, 0.999))
✓ Scheduler: CosineAnnealingLR (T_max=70, eta_min=1e-06)

[4/5] Starting training...
======================================================================
Training for 70 epochs
Checkpoints will be saved at epochs: [10, 30, 50, 70]
======================================================================

======================================================================
EPOCH [1/70]
======================================================================
  Batch [  50/546] - Loss: 0.125432 - Avg: 0.142156
  Batch [ 100/546] - Loss: 0.118234 - Avg: 0.135421
  ...
  Batch [ 546/546] - Loss: 0.112345 - Avg: 0.128765
======================================================================
Epoch [1/70] Complete - Average Loss: 0.128765
======================================================================

Learning rate: 0.000200 -> 0.000199

✓ Best model saved: weights/gopro_best.pth (Loss: 0.128765)
```

---

## 💾 Saved Checkpoints

After training, you'll have:

```
weights/
├── epoch_10.pth        ← Checkpoint at epoch 10
├── epoch_30.pth        ← Checkpoint at epoch 30
├── epoch_50.pth        ← Checkpoint at epoch 50
├── epoch_70.pth        ← Final checkpoint
└── gopro_best.pth      ← 🏆 Best model (lowest loss)
```

Each checkpoint contains:
- `model_state_dict` - Model weights
- `optimizer_state_dict` - Optimizer state
- `scheduler_state_dict` - Learning rate scheduler state
- `epoch` - Epoch number
- `loss` - Training loss

---

## 📝 Training Configuration Summary

| Parameter | Value | Purpose |
|-----------|-------|---------|
| **Dataset** | GOPRO_Large/train | Motion blur dataset |
| **Model** | MIMO-UNetPlus | Multi-scale deblurring |
| **Epochs** | 70 | Full training |
| **Batch Size** | 4 | GPU memory efficient |
| **Learning Rate** | 2e-4 | Standard for Adam |
| **LR Scheduler** | CosineAnnealing | Smooth decay |
| **Crop Size** | 256×256 | Random crop |
| **Loss** | L1Loss | Perceptual quality |
| **Optimizer** | Adam (β1=0.9, β2=0.999) | Adaptive learning |
| **num_workers** | 4 | Fast data loading |
| **pin_memory** | True | GPU transfer speed |

---

## 🎯 Why 70 Epochs of Long Training?

**Motion deblurring with MIMO-UNetPlus requires extended training (70 epochs vs. 30 for fine-tuning) because the model must learn complex multi-scale blur kernels from scratch across diverse motion patterns in the GoPro dataset.** Unlike fine-tuning where the model already understands deblurring fundamentals, training from random initialization requires the encoder to learn hierarchical feature extraction (edges → textures → objects), the decoder to learn multi-scale reconstruction, and the skip connections to preserve spatial details—all while handling camera shake, object motion, and varying blur intensities. The cosine annealing scheduler gradually reduces the learning rate from 2e-4 to 1e-6 over 70 epochs, allowing the model to make large exploratory updates early (epochs 1-30), refine features in mid-training (epochs 30-50), and converge to fine-grained optimal weights in late training (epochs 50-70), which is essential for achieving state-of-the-art deblurring performance on the challenging GoPro benchmark where motion blur varies significantly across 2,185 training image pairs.

---

## 🔄 Training Progress

### Early Training (Epochs 1-20):
- **Loss:** High (0.10-0.15)
- **Behavior:** Model learning basic features
- **Output:** Blurry but better than input
- **Learning rate:** High (2e-4 → 1.8e-4)

### Mid Training (Epochs 20-50):
- **Loss:** Decreasing (0.05-0.10)
- **Behavior:** Refining deblurring
- **Output:** Increasingly sharp
- **Learning rate:** Medium (1.8e-4 → 5e-5)

### Late Training (Epochs 50-70):
- **Loss:** Low (0.02-0.05)
- **Behavior:** Fine-tuning details
- **Output:** High-quality sharp images
- **Learning rate:** Low (5e-5 → 1e-6)

---

## 🛠️ Troubleshooting

### Error: "CUDA out of memory"
**Solution:** Reduce batch size in [train.py](train.py#L190)
```python
BATCH_SIZE = 2  # Change from 4 to 2
```

### Error: "No images found in GOPRO_Large/train"
**Solution:** Verify dataset structure:
```powershell
ls GOPRO_Large\train\
```
Should contain folders like `GOPR0372_07_00`, `GOPR0374_11_00`, etc.

### Training is very slow (using CPU)
**Solution:** Verify CUDA is available:
```powershell
python -c "import torch; print('CUDA:', torch.cuda.is_available())"
```
Should print: `CUDA: True`

### Learning rate not decreasing
**Solution:** This is normal! CosineAnnealingLR decreases gradually. Check logs—you should see small changes each epoch.

---

## 📈 Monitoring Training

### Loss Tracking:
- **Epoch 1:** ~0.12-0.15 (expected)
- **Epoch 10:** ~0.08-0.10
- **Epoch 30:** ~0.05-0.07
- **Epoch 50:** ~0.03-0.05
- **Epoch 70:** ~0.02-0.04

If loss plateaus or increases, training may need adjustment.

### Save Training Logs:
```powershell
python train.py > training_log.txt 2>&1
```

### Resume from Checkpoint (if training stops):
Currently not implemented in the script, but checkpoints contain all state needed to resume.

---

## 🎓 After Training Complete

### 1. Use the Best Model:
```powershell
python run_deblur.py --input blurry_image.jpg --output sharp.jpg --weights weights/gopro_best.pth
```

### 2. Test on GoPro Test Set:
```powershell
python run_deblur.py --input GOPRO_Large\test\GOPR0384_11_00\blur\000001.png --output test_result.png --weights weights/gopro_best.pth
```

### 3. Compare Different Epochs:
```powershell
# Test epoch 10
python run_deblur.py --input test.jpg --output result_ep10.jpg --weights weights/epoch_10.pth

# Test epoch 30
python run_deblur.py --input test.jpg --output result_ep30.jpg --weights weights/epoch_30.pth

# Test best
python run_deblur.py --input test.jpg --output result_best.jpg --weights weights/gopro_best.pth
```

---

## 💡 Pro Tips

1. **Start training overnight** - 8-16 hours is long!

2. **Monitor first epoch** - If batch processing is slow, something may be wrong

3. **Check GPU temperature** - Keep below 85°C; adjust fan/cooling if needed

4. **Use best model, not final** - `gopro_best.pth` usually better than `epoch_70.pth`

5. **Save logs** - Useful for debugging and analysis later

6. **Test periodically** - After epoch 30/50, test on sample images to see progress

7. **Backup checkpoints** - Copy to external drive; training takes hours!

---

## 🔬 Advanced: Training Features

### Random Crop Augmentation:
- Each epoch sees different 256×256 crops of the same images
- Effectively multiplies dataset size
- Prevents overfitting

### Multi-Scale Loss:
- MIMO-UNetPlus outputs 3 scales (coarse, medium, fine)
- Loss computed on all scales and summed
- Helps model learn hierarchical features

### Cosine Annealing:
- Learning rate follows cosine curve
- Smooth decay prevents abrupt changes
- Better convergence than step decay

### Gradient Accumulation:
- Not used (batch_size=4 fits in memory)
- Could enable by reducing batch_size and accumulating

---

## ❓ FAQ

**Q: Can I stop training early?**  
A: Yes, but 70 epochs is recommended for best quality. You can use checkpoints from epoch 30/50 if needed.

**Q: Why not use pretrained ImageNet weights?**  
A: MIMO-UNetPlus is task-specific; deblurring requires training from scratch on blur-sharp pairs.

**Q: Should I increase batch size?**  
A: RTX 3050 6GB can handle batch_size=4. Going higher may cause OOM errors.

**Q: Can I train on CPU?**  
A: Technically yes, but will take 50-100x longer (weeks instead of hours). GPU strongly recommended.

**Q: What if training loss increases?**  
A: Unusual but can happen. Check: data loading, GPU memory, learning rate. May need to restart.

---

## 📊 Comparison: Training vs Fine-Tuning

| Aspect | Training (GoPro) | Fine-Tuning (LOL) |
|--------|------------------|-------------------|
| Dataset | GOPRO_Large (2,185 pairs) | LOL_BLUR (489 pairs) |
| Epochs | 70 | 30 |
| Learning Rate | 2e-4 | 1e-5 |
| Scheduler | CosineAnnealing | None |
| Pretrained | ❌ No | ✅ Yes |
| Batch Size | 4 | 2 |
| Crop Strategy | Random 256×256 | Resize 256×256 |
| Time | 8-16 hours | 1-2 hours |
| Purpose | Motion deblurring | Low-light + blur |

---

## 🚀 Ready to Train?

**Just run:**
```powershell
python train.py
```

Training will automatically:
- ✅ Load 2,185 GoPro image pairs
- ✅ Create MIMO-UNetPlus model
- ✅ Train for 70 epochs with cosine LR decay
- ✅ Save checkpoints at epochs 10, 30, 50, 70
- ✅ Save best model continuously
- ✅ Use GPU acceleration

**Estimated completion:** 8-16 hours

**Good luck with your training!** 🎯
