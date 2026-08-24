# 🚂 Wagon Fine-Tuning Quick Start

## One-Command Training
```powershell
python train.py
```

## What It Does
✅ Loads wagon dataset from `train/train/blur/` and `train/train/sharp/`  
✅ Fine-tunes MIMOUNetPlus from `weights/gopro_pretrained.pth`  
✅ Trains for 20 epochs with batch size 2  
✅ Saves checkpoints: `wagon_epoch_10.pth`, `wagon_epoch_20.pth`, `wagon_best.pth`  

## Check GPU Usage
```powershell
nvidia-smi -l 1
```
Should show 80-100% GPU utilization and ~4-5 GB VRAM usage.

## Expected Time
⏱️ ~40-80 minutes total (2-4 min per epoch)

## Key Settings
- **Learning Rate**: 1e-5 (fine-tuning)
- **Batch Size**: 2 (6GB VRAM safe)
- **Crop Size**: 256×256
- **Optimizer**: Adam
- **Loss**: L1Loss

## After Training
Best model saved to: **`weights/wagon_best.pth`**

Use it for inference on new wagon images!

---

## Why Fine-Tuning?

**Fine-tuning** = Starting with pre-trained GoPro weights → Adapt to wagon dataset

**Benefits**:
- 🚀 **Faster**: 20 epochs vs 100+ from scratch
- 📊 **Better quality**: Leverages learned blur/sharp patterns
- 💾 **Less data needed**: Works with small datasets (50 images)
- 🎯 **Lower learning rate**: Gentle adjustment (1e-5 vs 2e-4)

**Analogy**: Teaching an experienced chef a new recipe (fine-tuning) vs. teaching cooking to a beginner (from scratch).

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "CUDA out of memory" | Set `BATCH_SIZE = 1` in train.py line 220 |
| "No image pairs found" | Check `train/train/blur/` and `train/train/sharp/` exist |
| "Pretrained weights not found" | Copy `gopro_best.pth` to `gopro_pretrained.pth` |
| GPU not used | Reinstall PyTorch with CUDA support |

---

📖 **Full Guide**: See `WAGON_FINETUNING_GUIDE.md`
