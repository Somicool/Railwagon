# Fine-tuning MIMOUNetPlus Guide

## Dataset Structure
Your dataset is ready at: `train/train/`
- **Blur images**: `train/train/blur/` (1066 images)
- **Sharp images**: `train/train/sharp/` (1066 images)

## Quick Start

### 1. Basic Training (GPU recommended)
```bash
python finetune_mimo.py --epochs 50 --batch_size 4
```

### 2. Training with Custom Settings
```bash
python finetune_mimo.py \
    --train_blur train/train/blur \
    --train_sharp train/train/sharp \
    --batch_size 8 \
    --patch_size 256 \
    --epochs 100 \
    --lr 0.0001 \
    --val_split 0.1 \
    --save_dir checkpoints
```

### 3. Resume Training
```bash
python finetune_mimo.py --resume checkpoints/latest.pth --epochs 150
```

### 4. Fine-tune from Pretrained
```bash
python finetune_mimo.py --pretrained weights/MIMO-UNetPlus.pkl --epochs 50
```

## Training Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--train_blur` | `train/train/blur` | Path to blur images |
| `--train_sharp` | `train/train/sharp` | Path to sharp images |
| `--batch_size` | `4` | Batch size (reduce if OOM) |
| `--patch_size` | `256` | Training patch size |
| `--epochs` | `100` | Number of training epochs |
| `--lr` | `0.0001` | Learning rate |
| `--val_split` | `0.1` | Validation split (10%) |
| `--save_dir` | `checkpoints` | Save directory |
| `--num_workers` | `4` | Data loading workers |
| `--pretrained` | `weights/MIMO-UNetPlus.pkl` | Pretrained weights |
| `--resume` | `None` | Resume checkpoint |

## Output Files

Training creates three types of checkpoints in `checkpoints/`:
- **`best.pth`** - Best model based on validation PSNR (full checkpoint)
- **`best_model.pkl`** - Best model weights only (for inference)
- **`latest.pth`** - Latest epoch (for resuming)
- **`epoch_X.pth`** - Periodic checkpoints (every 10 epochs)

## Testing Fine-tuned Model

### Test on single image
```bash
python test_finetuned_model.py \
    --model checkpoints/best_model.pkl \
    --images train/train/blur/3821852741-preview_frame_00001.jpg
```

### Test on multiple images
```bash
python test_finetuned_model.py \
    --model checkpoints/best.pth \
    --images image1.jpg image2.jpg image3.jpg \
    --output deblurred_results
```

## Training Tips

### GPU Memory Issues
If you encounter CUDA OOM errors:
```bash
python finetune_mimo.py --batch_size 2 --patch_size 128
```

### CPU Training (slower)
```bash
python finetune_mimo.py --batch_size 1 --num_workers 0 --epochs 20
```

### Fast Testing Run
```bash
python finetune_mimo.py --epochs 5 --batch_size 2 --val_split 0.2
```

## Expected Training Time

- **GPU (RTX 3080)**: ~2-3 hours for 50 epochs
- **GPU (RTX 2060)**: ~4-5 hours for 50 epochs  
- **CPU**: ~24-48 hours for 50 epochs (not recommended)

## Monitoring Training

The training script shows:
- **Training Progress**: Loss and PSNR per batch
- **Epoch Summary**: Average train/val loss and PSNR
- **Best Model**: Automatically saved when validation PSNR improves
- **Learning Rate**: Current LR (decreases with cosine schedule)

Example output:
```
Epoch 10/100
Train - Loss: 0.0234, PSNR: 28.45 dB
Valid - Loss: 0.0198, PSNR: 29.12 dB
LR: 0.000087
★ New best model saved! PSNR: 29.12 dB
```

## Data Augmentation

The training automatically applies:
- ✓ Random crops (256x256 patches)
- ✓ Horizontal flips
- ✓ Vertical flips
- ✓ 90° rotations

## Multi-Scale Loss

The model outputs 3 scales and uses weighted loss:
- Scale 1 (full): weight = 1.0
- Scale 2 (1/2): weight = 0.6
- Scale 3 (1/4): weight = 0.4

## Validation

- 10% of data used for validation (adjustable with `--val_split`)
- Validation runs after each epoch
- No augmentation on validation set
- Best model saved based on validation PSNR

## Next Steps After Training

1. **Test the model**:
   ```bash
   python test_finetuned_model.py --model checkpoints/best_model.pkl --images test_image.jpg
   ```

2. **Use in your pipeline**:
   ```python
   from models.mimo_unet_plus import MIMOUNetPlus
   model = MIMOUNetPlus()
   model.load_state_dict(torch.load('checkpoints/best_model.pkl'))
   ```

3. **Compare with pretrained**:
   Test both pretrained and fine-tuned models to see improvement

## Troubleshooting

### Issue: "CUDA out of memory"
**Solution**: Reduce batch size or patch size
```bash
python finetune_mimo.py --batch_size 2 --patch_size 128
```

### Issue: Training is too slow
**Solution**: Increase workers or reduce epochs
```bash
python finetune_mimo.py --num_workers 8 --epochs 30
```

### Issue: Validation PSNR not improving
**Solution**: 
- Check if data is properly paired
- Reduce learning rate: `--lr 0.00005`
- Increase epochs: `--epochs 150`

### Issue: Model overfitting
**Solution**: Increase validation split
```bash
python finetune_mimo.py --val_split 0.2
```

## Example: Complete Training Workflow

```bash
# 1. Start training
python finetune_mimo.py --epochs 100 --batch_size 4

# 2. If interrupted, resume
python finetune_mimo.py --resume checkpoints/latest.pth --epochs 150

# 3. Test best model
python test_finetuned_model.py \
    --model checkpoints/best_model.pkl \
    --images train/train/blur/3821852741-preview_frame_00001.jpg \
    --output results

# 4. Use in production
python run_deblur.py --model checkpoints/best_model.pkl --image my_image.jpg
```

## Notes

- Training uses **Charbonnier Loss** (smooth L1)
- **AdamW optimizer** with weight decay
- **Cosine annealing** learning rate schedule
- **PSNR metric** for evaluation
- All checkpoints include full training state for resuming
