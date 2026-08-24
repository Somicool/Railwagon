# 🚀 QUICK START - LOL_BLUR Fine-Tuning

## Run Training (3 Steps)

### 1️⃣ Activate Environment
```powershell
cd C:\Users\Soham\OneDrive\Desktop\blur
.\venv\Scripts\Activate.ps1
```

### 2️⃣ Start Fine-Tuning
```powershell
python train.py
```

### 3️⃣ Monitor GPU (Optional - Open New PowerShell)
```powershell
nvidia-smi -l 1
```

---

## ⚙️ Configuration at a Glance

```python
# Dataset
DATA_ROOT = 'LOL_BLUR'
PRETRAINED_WEIGHTS = 'weights/mimo_unetplus_gopro_trained.pth'

# Hyperparameters
IMAGE_SIZE = 256
BATCH_SIZE = 2
LEARNING_RATE = 1e-5
NUM_EPOCHS = 30

# Hardware
DEVICE = 'cuda' (GPU)
NUM_WORKERS = 2
PIN_MEMORY = True

# Loss & Optimizer
LOSS = L1Loss
OPTIMIZER = Adam
```

---

## 📦 Outputs

Training will create:

```
weights/
├── lol_epoch_10.pth    ← Checkpoint at epoch 10
├── lol_epoch_20.pth    ← Checkpoint at epoch 20  
├── lol_epoch_30.pth    ← Checkpoint at epoch 30
└── lol_best.pth        ← 🏆 Best model (use this!)
```

---

## ⏱️ Expected Duration

- **Per Epoch**: ~2-4 minutes
- **Total (30 epochs)**: ~60-120 minutes
- **Dataset Size**: 489 image pairs
- **GPU**: NVIDIA RTX 3050 6GB

---

## 🎯 Why Fine-Tuning?

**Instead of training from scratch:**
- ✅ Uses pretrained GoPro weights as starting point
- ✅ Faster convergence (30 epochs vs 100+)
- ✅ Needs less data (489 images vs 10,000+)
- ✅ Better results with small datasets
- ✅ Lower learning rate (1e-5) preserves learned features

**Think of it as:** Teaching an expert deblurrer to handle low-light conditions!

---

## 🔍 Verify GPU is Working

**Before training:**
```powershell
python -c "import torch; print('CUDA Available:', torch.cuda.is_available())"
```
Should print: `CUDA Available: True`

**During training:**
```powershell
nvidia-smi
```
Look for:
- GPU Utilization: 80-100%
- Memory Used: ~2-4 GB / 6 GB

---

## 🎓 After Training

### Use the fine-tuned model:
```powershell
python run_deblur.py --input lowlight_blurry.jpg --output sharp.jpg --weights weights/lol_best.pth
```

### Compare with pretrained model:
```powershell
# GoPro model
python run_deblur.py --input test.jpg --output gopro_result.jpg --weights weights/mimo_unetplus_gopro_trained.pth

# Fine-tuned LOL model
python run_deblur.py --input test.jpg --output lol_result.jpg --weights weights/lol_best.pth
```

---

## 🛠️ Troubleshooting

| Issue | Solution |
|-------|----------|
| CUDA out of memory | Set `BATCH_SIZE = 1` in [train.py](train.py#L181) |
| No images found | Check `LOL_BLUR/train/blur/` and `sharp/` exist |
| Can't find weights | Verify `weights/mimo_unetplus_gopro_trained.pth` exists |
| Training on CPU | Install PyTorch with CUDA support |

---

## 📊 Understanding the Output

```
Epoch [1/30]
------------------------------------------------------------
  Batch [10/245] - Loss: 0.045321    ← L1 loss (lower is better)
  Batch [20/245] - Loss: 0.042156
  ...
============================================================
Epoch [1/30] - Average Loss: 0.042156    ← Epoch average
============================================================

✓ Best model saved: weights/lol_best.pth (Loss: 0.042156)
```

**Good loss values:** 0.02 - 0.04  
**Loss decreasing?** ✅ Model is learning!  
**Loss plateaued?** Training converged (can stop early)

---

## 📝 Files Modified

- ✅ [train.py](train.py) - Complete fine-tuning script
- ✅ [FINETUNING_GUIDE.md](FINETUNING_GUIDE.md) - Detailed documentation
- ✅ [QUICK_START.md](QUICK_START.md) - This file

---

## 💡 Pro Tips

1. **Save logs**: `python train.py > training_log.txt 2>&1`
2. **Stop early**: Press `Ctrl+C` after epoch completes (best model already saved)
3. **Use best model**: `lol_best.pth` usually better than `lol_epoch_30.pth`
4. **Test periodically**: Check results every 10 epochs

---

**Ready? Just run:** `python train.py` 🚀
