# MIMO-UNetPlus Fine-Tuning Guide for LOL_BLUR Dataset

## ✅ Project Overview

You now have a complete fine-tuning script that:
- ✓ Loads pretrained MIMO-UNetPlus from GoPro training
- ✓ Fine-tunes on LOL_BLUR (low-light + motion blur dataset)
- ✓ Uses all your specified requirements (L1Loss, Adam, lr=1e-5, etc.)
- ✓ Saves checkpoints at epochs 10, 20, 30 and best model

---

## 🚀 How to Run Training

### 1. Activate Virtual Environment
```powershell
cd C:\Users\Soham\OneDrive\Desktop\blur
.\venv\Scripts\Activate.ps1
```

### 2. Start Fine-Tuning
```powershell
python train.py
```

**That's it!** The script will automatically:
- Detect and use your GPU (NVIDIA RTX 3050)
- Load 489 image pairs from LOL_BLUR/train
- Load pretrained weights from `weights/mimo_unetplus_gopro_trained.pth`
- Fine-tune for 30 epochs
- Save checkpoints automatically

---

## 📊 Expected Output

```
============================================================
MIMO-UNETPLUS FINE-TUNING ON LOL_BLUR DATASET
============================================================
Device: cuda
GPU: NVIDIA GeForce RTX 3050 Laptop GPU
GPU Memory: 6.00 GB
============================================================

[1/5] Loading dataset...

============================================================
Loading train dataset from: LOL_BLUR
============================================================
✓ Loaded 489 image pairs
============================================================

✓ Dataset loaded successfully
  - Total training samples: 489
  - Batch size: 2
  - Batches per epoch: 245

[2/5] Loading model...
Loading pretrained weights from: weights/mimo_unetplus_gopro_trained.pth
✓ Pretrained weights loaded successfully
✓ Model moved to cuda

[3/5] Setting up training components...
✓ Loss function: L1Loss
✓ Optimizer: Adam (lr=1e-05)

[4/5] Starting fine-tuning...
============================================================

Epoch [1/30]
------------------------------------------------------------
  Batch [10/245] - Loss: 0.045321
  Batch [20/245] - Loss: 0.042156
  ...
```

---

## 💾 Saved Checkpoints

After training completes, you'll have:

```
weights/
├── lol_epoch_10.pth      ← Checkpoint at epoch 10
├── lol_epoch_20.pth      ← Checkpoint at epoch 20
├── lol_epoch_30.pth      ← Checkpoint at epoch 30
└── lol_best.pth          ← Best model (lowest loss)
```

Each checkpoint contains:
- Model weights (`model_state_dict`)
- Optimizer state (`optimizer_state_dict`)
- Epoch number
- Loss value

---

## 🔍 Monitor GPU Usage During Training

### Option 1: Real-time GPU Monitoring
Open a **new PowerShell window** and run:

```powershell
nvidia-smi -l 1
```

This updates every 1 second and shows:
- GPU utilization percentage
- Memory usage (expect ~2-4 GB for batch_size=2)
- Temperature
- Power consumption

### Option 2: Single GPU Check
```powershell
nvidia-smi
```

### What to Look For:
- **GPU Utilization**: Should be 80-100% during training
- **Memory Usage**: ~2-4 GB / 6 GB
- **Temperature**: Should stay under 85°C

---

## ⏱️ Training Time Estimate

- **Batches per epoch**: 245 (489 images ÷ batch_size 2)
- **Time per batch**: ~0.5-1 second on RTX 3050
- **Time per epoch**: ~2-4 minutes
- **Total training time**: ~60-120 minutes (30 epochs)

---

## 🎯 Why Fine-Tuning Instead of Training from Scratch?

### Fine-Tuning Benefits:

1. **Transfer Learning**
   - Model already learned general deblurring from GoPro dataset
   - Only needs to adapt to low-light conditions
   - Faster convergence

2. **Less Data Required**
   - Pretrained weights provide strong initialization
   - Can achieve good results with 489 images
   - Training from scratch would need 10,000+ images

3. **Lower Learning Rate (1e-5 vs 1e-4)**
   - Smaller updates preserve learned features
   - Prevents catastrophic forgetting
   - Fine-tunes rather than overwrites weights

4. **Computational Efficiency**
   - 30 epochs vs 100+ epochs from scratch
   - Less GPU time and electricity
   - Faster experimentation

### The Process:
```
Pretrained Model (GoPro)
         ↓
    Fine-tuning (LOL_BLUR)
         ↓
  Specialized Model (Low-Light Deblurring)
```

---

## 🛠️ Troubleshooting

### Error: "CUDA out of memory"
**Solution**: Reduce batch size in [train.py](train.py#L175)
```python
BATCH_SIZE = 1  # Change from 2 to 1
```

### Error: "No matching image pairs found"
**Solution**: Verify dataset structure:
```powershell
ls LOL_BLUR\train\blur\
ls LOL_BLUR\train\sharp\
```
Both folders should have the same filenames.

### Error: "Cannot find pretrained weights"
**Solution**: Check the weights file exists:
```powershell
ls weights\mimo_unetplus_gopro_trained.pth
```

### Training is very slow
**Solution**: Confirm GPU is being used:
```powershell
python -c "import torch; print('CUDA:', torch.cuda.is_available())"
```
Should print: `CUDA: True`

---

## 📝 Configuration Summary

| Parameter | Value | Location in Code |
|-----------|-------|------------------|
| Dataset | LOL_BLUR | Line 175 |
| Pretrained Weights | `weights/mimo_unetplus_gopro_trained.pth` | Line 176 |
| Image Size | 256 × 256 | Line 180 |
| Batch Size | 2 | Line 181 |
| Learning Rate | 1e-5 | Line 182 |
| Epochs | 30 | Line 183 |
| Loss Function | L1Loss | Line 238 |
| Optimizer | Adam | Line 239 |
| num_workers | 2 | Line 184 |
| pin_memory | True (GPU) | Line 211 |

---

## 🎓 Next Steps After Training

### 1. Use the Fine-Tuned Model
```powershell
python run_deblur.py --input blurry_lowlight.jpg --output sharp.jpg --weights weights/lol_best.pth
```

### 2. Compare Models
Test both pretrained and fine-tuned models:
```powershell
# Original GoPro model
python run_deblur.py --input test.jpg --output output_gopro.jpg --weights weights/mimo_unetplus_gopro_trained.pth

# Fine-tuned LOL model
python run_deblur.py --input test.jpg --output output_lol.jpg --weights weights/lol_best.pth
```

### 3. Evaluate on Test Set
Modify inference script to process entire LOL_BLUR/test/ folder

---

## 📚 Key Files

| File | Purpose |
|------|---------|
| [train.py](train.py) | Main fine-tuning script |
| [models/mimo_official.py](models/mimo_official.py) | MIMOUNetPlus architecture |
| `weights/mimo_unetplus_gopro_trained.pth` | Pretrained weights |
| `LOL_BLUR/train/` | Training dataset |
| `weights/lol_best.pth` | Best fine-tuned model (created after training) |

---

## 🔬 Understanding the Output

### Batch Progress
```
Batch [10/245] - Loss: 0.045321
```
- Current batch number / Total batches
- L1 Loss between predicted and ground truth images
- Lower is better (target: < 0.03)

### Epoch Summary
```
Epoch [1/30] - Average Loss: 0.042156
```
- Average loss across all 245 batches
- Track this to monitor convergence

### Checkpoint Messages
```
✓ Checkpoint saved: weights/lol_epoch_10.pth
✓ Best model saved: weights/lol_best.pth (Loss: 0.028456)
```
- Confirms successful saves
- Best model updates whenever loss improves

---

## 💡 Pro Tips

1. **Monitor Loss Curve**
   - Loss should decrease over epochs
   - If loss plateaus, training has converged
   - Typical final loss: 0.02-0.04

2. **Use Best Model, Not Final**
   - `lol_best.pth` is usually better than `lol_epoch_30.pth`
   - Model can overfit in later epochs

3. **Save Training Logs**
   ```powershell
   python train.py > training_log.txt 2>&1
   ```

4. **Test During Training**
   - Pause training (Ctrl+C after epoch completes)
   - Test current best model
   - Resume if needed (requires modification)

---

## ❓ FAQ

**Q: Can I stop training early?**  
A: Yes! Press `Ctrl+C` after an epoch completes. The best model is already saved.

**Q: Can I resume training from epoch 30?**  
A: Not with current script, but checkpoints contain optimizer state for resuming.

**Q: Should I fine-tune longer?**  
A: 30 epochs is usually enough. Monitor loss - if still decreasing, consider 40-50 epochs.

**Q: Can I use this on CPU?**  
A: Technically yes, but it will be 50-100x slower. GPU strongly recommended.

**Q: What if I get different results?**  
A: Normal! Training involves randomness (data shuffling, weight initialization). Results will vary slightly.

---

## 📧 Support

If you encounter issues:
1. Check error message carefully
2. Verify dataset structure matches requirements
3. Confirm GPU is available (`nvidia-smi`)
4. Check that pretrained weights exist

---

**🎉 Ready to start fine-tuning? Run:** `python train.py`
