# MIMO-UNet Image Deblurring 🔍

A **simple, hackathon-friendly** implementation of an image deblurring model inspired by MIMO-UNet (CVPR 2021).

Perfect for:
- 🎓 Learning computer vision and deep learning
- 🏆 Hackathon demos and projects
- 🧪 Quick experimentation with image restoration
- 📚 Understanding encoder-decoder architectures

## 📋 Features

- ✅ Clean, minimal PyTorch implementation
- ✅ Well-commented code for beginners
- ✅ Simple command-line interface
- ✅ CPU and GPU support
- ✅ No external dependencies on GitHub repos

## 🏗️ Architecture

The model uses a **U-Net style encoder-decoder** architecture:

```
Input Image (Blurry)
    ↓
Encoder (Downsampling)
    → 32 → 64 → 128 → 256 channels
    ↓
Bottleneck (512 channels)
    ↓
Decoder (Upsampling + Skip Connections)
    ← 256 ← 128 ← 64 ← 32
    ↓
Output Image (Sharp)
```

**Key Components:**
- **Encoder**: Captures image context at multiple scales
- **Skip Connections**: Preserves fine details during upsampling
- **Decoder**: Reconstructs sharp image from deep features

## 📁 Project Structure

```
blur/
├── models/
│   └── mimo_unet.py          # Model architecture
├── weights/
│   └── mimo_unet.pth         # Pretrained weights (you need to add this)
├── run_deblur.py             # Inference script
├── requirements.txt          # Dependencies
└── README.md                 # This file
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Or install manually:
```bash
pip install torch torchvision opencv-python numpy
```

### 2. Add Pretrained Weights

⚠️ **Important**: You need to provide pretrained weights!

**Option A - Use existing weights:**
- Download pretrained deblurring weights (e.g., from GoPro dataset training)
- Place the `.pth` file in `weights/mimo_unet.pth`

**Option B - Train your own:**
- Train the model on a deblurring dataset (GoPro, REDS, etc.)
- Save the model's state_dict as `weights/mimo_unet.pth`

**Option C - Test without weights:**
- The script will run with random weights (for architecture testing only)
- Results will not be meaningful without trained weights

### 3. Run Deblurring

```bash
python run_deblur.py --input blurry_image.jpg --output deblurred_image.jpg
```

**Arguments:**
- `--input` or `-i`: Path to your blurry input image
- `--output` or `-o`: Path to save the deblurred result
- `--weights` or `-w`: (Optional) Custom path to weights file

## 💡 Usage Examples

### Basic Usage
```bash
python run_deblur.py -i test_images/blurry.jpg -o results/sharp.jpg
```

### With Custom Weights Path
```bash
python run_deblur.py -i input.png -o output.png -w my_custom_weights.pth
```

### Test the Architecture
```bash
cd models
python mimo_unet.py
```
This will verify the model architecture and print parameter count.

## 🧠 How It Works

### 1. **Image Loading** ([run_deblur.py](run_deblur.py))
- Reads image with OpenCV
- Converts BGR → RGB
- Normalizes to [-1, 1] range
- Converts to PyTorch tensor

### 2. **Model Processing** ([models/mimo_unet.py](models/mimo_unet.py))
- **Encoder**: Progressively downsamples image to extract features
- **Bottleneck**: Processes features at lowest resolution
- **Decoder**: Upsamples while using skip connections for details
- **Output**: Generates deblurred image

### 3. **Image Saving**
- Denormalizes from [-1, 1] to [0, 255]
- Converts RGB → BGR
- Saves with OpenCV

## 📊 Model Details

| Component | Details |
|-----------|---------|
| **Input** | RGB image (any size) |
| **Output** | Deblurred RGB image (same size) |
| **Parameters** | ~7.8 million |
| **Architecture** | U-Net with 4 encoder/decoder levels |
| **Activation** | ReLU (hidden), Tanh (output) |

## 🎓 Understanding the Code

### Key Files Explained:

#### `models/mimo_unet.py`
Contains three main classes:
- **`DownsampleBlock`**: Reduces image size, extracts features
- **`UpsampleBlock`**: Increases size, combines with skip connections
- **`MIMOUNet`**: Main model connecting all blocks

#### `run_deblur.py`
Main inference script with:
- `load_image()`: Preprocessing pipeline
- `save_image()`: Postprocessing pipeline
- `deblur_image()`: Complete inference workflow

## 🔧 Customization

### Modify Architecture Depth
In [models/mimo_unet.py](models/mimo_unet.py), adjust encoder/decoder blocks:
```python
# Add more downsampling layers
self.down4 = DownsampleBlock(256, 512)

# Add corresponding upsampling
self.up0 = UpsampleBlock(1024, 512)
```

### Change Channel Sizes
Modify the channel numbers in `__init__`:
```python
self.input_conv = nn.Sequential(
    nn.Conv2d(in_channels, 64, ...),  # Changed from 32 to 64
    ...
)
```

## 🐛 Troubleshooting

### "Weights file not found"
- Ensure `weights/mimo_unet.pth` exists
- Or provide custom path with `--weights`

### "Could not read image"
- Check image path is correct
- Supported formats: jpg, png, bmp, tiff

### CUDA out of memory
- Process smaller images
- Use CPU: The model automatically falls back to CPU if GPU unavailable

### Poor deblurring results
- Ensure you're using **trained weights**, not random initialization
- Weights should be trained on similar blur types as your test images

## 📚 Learning Resources

**What is MIMO-UNet?**
- Paper: [Rethinking Coarse-to-Fine Approach in Single Image Deblurring](https://arxiv.org/abs/2105.04235)
- Key idea: Multi-scale input/output processing

**Understanding U-Net:**
- Original paper: [U-Net: Convolutional Networks for Biomedical Image Segmentation](https://arxiv.org/abs/1505.04597)
- Skip connections preserve spatial information

## ⚖️ License

This is a simplified educational implementation. For production use or research, please:
- Cite the original MIMO-UNet paper if you use this architecture
- Follow PyTorch's license terms
- Ensure your pretrained weights are properly licensed

## 🤝 Contributing

This is a hackathon-friendly template. Feel free to:
- Extend the architecture
- Add data augmentation
- Implement training code
- Create your own datasets

## 📮 Support

For questions about:
- **PyTorch**: Check [PyTorch documentation](https://pytorch.org/docs/)
- **OpenCV**: See [OpenCV tutorials](https://docs.opencv.org/)
- **Model architecture**: Review comments in [models/mimo_unet.py](models/mimo_unet.py)

---

**Happy deblurring! 🎯**

Made with ❤️ for hackathons and learning
