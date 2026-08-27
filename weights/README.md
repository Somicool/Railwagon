# Weights Directory

This directory should contain your pretrained model weights.

## Required File
`mimo_unet.pth` - Pretrained MIMO-UNet weights

## How to Get Weights

### Option 1: Download Pretrained Weights
If you have access to pretrained deblurring weights:
1. Download the `.pth` file
2. Rename it to `mimo_unet.pth`
3. Place it in this directory

### Option 2: Train Your Own Model
1. Prepare a deblurring dataset (e.g., GoPro, REDS, HIDE)
2. Train the MIMO-UNet model
3. Save the model's state_dict:
   ```python
   torch.save(model.state_dict(), 'weights/mimo_unet.pth')
   ```

### Option 3: Test Mode (No Weights)
The inference script will work without weights (using random initialization) for testing purposes only. Results won't be meaningful without trained weights.

## Weight File Format

The weights should be a PyTorch state dict saved with `torch.save()`:

```python
# Minimal format
torch.save(model.state_dict(), 'mimo_unet.pth')

# Or with additional info
torch.save({
    'model_state_dict': model.state_dict(),
    'epoch': epoch,
    'loss': loss,
}, 'mimo_unet.pth')
```

## File Size
Expected weight file size: ~30-40 MB (depending on precision)

---

**Note**: Pretrained weights are not included in this repository. You must obtain or train them separately.
