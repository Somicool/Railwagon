# MIMOUNetPlus Fine-tuning - Quick Reference

## ✅ Dataset Status
- **Location**: `train/train/`
- **Blur images**: 1066 images (898×506)
- **Sharp images**: 1066 images (898×506)
- **Status**: ✓ Ready for training

## 🚀 Start Training

### Option 1: Double-click batch file
```
START_FINETUNING.bat
```

### Option 2: Command line (default settings)
```bash
python finetune_mimo.py
```

### Option 3: Custom settings
```bash
python finetune_mimo.py --epochs 100 --batch_size 8 --lr 0.0001
```

## 📊 Key Parameters

| Setting | Default | Recommended |
|---------|---------|-------------|
| Epochs | 50 | 50-100 |
| Batch Size | 4 | 4-8 (GPU), 1-2 (CPU) |
| Learning Rate | 0.0001 | 0.0001 |
| Patch Size | 256 | 256 |
| Validation Split | 10% | 10% |

## 💾 Training Outputs

All saved in `checkpoints/`:
- `best_model.pkl` - Best model (use this!)
- `best.pth` - Best checkpoint (includes optimizer state)
- `latest.pth` - Latest epoch (for resuming)

## 🔄 Resume Training
```bash
python finetune_mimo.py --resume checkpoints/latest.pth --epochs 150
```

## 🧪 Test Fine-tuned Model

### Single image
```bash
python test_finetuned_model.py --model checkpoints/best_model.pkl --images test.jpg
```

### Multiple images
```bash
python test_finetuned_model.py --model checkpoints/best_model.pkl --images img1.jpg img2.jpg img3.jpg
```

## 📈 Compare Results
```bash
python compare_results.py --model checkpoints/best_model.pkl --num_samples 10
```

This creates side-by-side comparisons: Blur | Deblurred | Sharp (GT)

## 🔧 Troubleshooting

### CUDA Out of Memory
```bash
python finetune_mimo.py --batch_size 2 --patch_size 128
```

### CPU Training (slow but works)
```bash
python finetune_mimo.py --batch_size 1 --num_workers 0 --epochs 20
```

### Quick test (5 epochs)
```bash
python finetune_mimo.py --epochs 5 --batch_size 2
```

## 📝 Training Progress

Watch for:
- **Train PSNR**: Should increase (target: 30+ dB)
- **Val PSNR**: Should increase (best models saved automatically)
- **Loss**: Should decrease
- **★ Symbol**: Indicates new best model saved

Example:
```
Epoch 25/50
Train - Loss: 0.0187, PSNR: 30.24 dB
Valid - Loss: 0.0165, PSNR: 31.18 dB
LR: 0.000073
★ New best model saved! PSNR: 31.18 dB
```

## ⏱️ Expected Time

| Hardware | Time (50 epochs) |
|----------|------------------|
| RTX 3080 | ~2-3 hours |
| RTX 2060 | ~4-5 hours |
| GTX 1660 | ~6-8 hours |
| CPU | ~24-48 hours ❌ |

## 📂 Files Created

### Training Scripts
- `finetune_mimo.py` - Main training script
- `START_FINETUNING.bat` - Quick start script
- `check_dataset.py` - Verify dataset

### Testing Scripts
- `test_finetuned_model.py` - Test on images
- `compare_results.py` - Visual comparisons

### Guides
- `FINETUNING_README.md` - Complete guide
- `FINETUNING_QUICK_REF.md` - This file

## 🎯 Recommended Workflow

1. **Check dataset** (done ✓)
   ```bash
   python check_dataset.py --visualize
   ```

2. **Start training**
   ```bash
   START_FINETUNING.bat
   ```
   or
   ```bash
   python finetune_mimo.py --epochs 50 --batch_size 4
   ```

3. **Monitor progress**
   - Watch terminal for PSNR improvements
   - Training auto-saves best model
   - Can interrupt and resume anytime

4. **Test results**
   ```bash
   python compare_results.py --model checkpoints/best_model.pkl --num_samples 5
   ```

5. **Use in production**
   ```python
   from models.mimo_unet_plus import MIMOUNetPlus
   import torch
   
   model = MIMOUNetPlus()
   model.load_state_dict(torch.load('checkpoints/best_model.pkl'))
   model.eval()
   ```

## 💡 Tips

- **First time**: Start with 5 epochs to test setup
- **GPU memory**: Reduce batch_size if OOM error
- **Best results**: Train for 100+ epochs
- **Resume anytime**: Use `--resume checkpoints/latest.pth`
- **Compare models**: Test both pretrained and fine-tuned

## 🆘 Common Issues

| Problem | Solution |
|---------|----------|
| CUDA OOM | `--batch_size 2 --patch_size 128` |
| Too slow | `--num_workers 8` or reduce epochs |
| No improvement | Increase epochs or reduce LR |
| Dataset error | Run `python check_dataset.py` |

## 📞 Need Help?

Check the complete guide: [FINETUNING_README.md](FINETUNING_README.md)

---

**Ready to start?** Just run: `START_FINETUNING.bat` or `python finetune_mimo.py`
