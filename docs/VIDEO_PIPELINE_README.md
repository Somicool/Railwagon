# Video-to-Wagon-OCR Pipeline

**Automated Railway Wagon Inspection System**  
Process train videos and extract wagon numbers using temporal fusion and OCR.

---

## 🎯 Overview

This pipeline automates the extraction of wagon numbers from railway inspection videos by:
1. Extracting frames at configurable FPS
2. Applying deblurring enhancement
3. Isolating wagon number regions
4. **Fusing multiple frames temporally** to reduce blur and noise
5. Applying OCR-specific enhancement
6. Running OCR to extract wagon numbers

---

## 📋 Requirements

### Python Packages
```bash
pip install torch torchvision opencv-python numpy tqdm easyocr
```

**Optional (for Tesseract OCR):**
```bash
pip install pytesseract
# Also install Tesseract executable: https://github.com/tesseract-ocr/tesseract
```

### Pretrained Model
- Place your trained deblurring model in `weights/` folder
- Example: `weights/gopro_best.pth`

---

## 🚀 Quick Start

### Basic Usage
```bash
python run_video_pipeline.py train_video.mp4 weights/gopro_best.pth
```

### Custom Settings
```bash
python run_video_pipeline.py train_video.mp4 weights/gopro_best.pth \
    --output my_results \
    --fps 10 \
    --window 5 \
    --ocr easyocr \
    --confidence 0.3 \
    --device cuda
```

### Command-Line Options
```
positional arguments:
  video                 Path to input video file (MP4)
  model                 Path to deblurring model weights (.pth)

optional arguments:
  -o, --output DIR      Output directory (default: results)
  --fps FPS             Target frame extraction rate (default: 5)
  -w, --window SIZE     Temporal fusion window 3-5 (default: 3)
  --ocr ENGINE          OCR engine: easyocr or tesseract (default: easyocr)
  -c, --confidence THR  Min OCR confidence 0.0-1.0 (default: 0.3)
  --device DEVICE       cuda or cpu (default: cuda)
```

---

## 📁 Output Structure

After running the pipeline, you'll get:

```
results/
├── 1_raw_frames/           # Extracted video frames (5 FPS default)
│   ├── frame_0001.png
│   ├── frame_0002.png
│   └── ...
│
├── 2_enhanced_frames/      # Deblurred frames
│   ├── frame_0001.png
│   └── ...
│
├── 3_band_frames/          # Wagon number search bands (40-60% height)
│   ├── frame_0001.png
│   └── ...
│
├── 4_fused/                # Temporally fused images (median of 3-5 frames)
│   ├── fused_0001.png
│   └── ...
│
├── 5_enhanced_text/        # OCR-optimized (CLAHE + sharpening)
│   ├── fused_0001_color.png
│   ├── fused_0001_gray.png
│   └── ...
│
└── 6_ocr_results/          # Final OCR outputs
    ├── ocr_results.json    # Detailed JSON with bboxes and confidences
    ├── ocr_results.txt     # Human-readable wagon numbers
    └── ocr_visuals/        # Images with OCR bounding boxes
        ├── fused_0001_gray_ocr.png
        └── ...
```

---

## 🔬 Why Temporal Fusion?

### The Problem
In high-speed railway wagon inspection:
- **Motion blur** varies across frames due to camera shake and train speed
- **Noise** from low-light conditions
- **Reflections and shadows** can obscure text
- Single-frame enhancement has limited effectiveness

### The Solution: Temporal Fusion
By combining information from **multiple consecutive frames**:

1. **Different blur patterns**: Each frame has slightly different motion blur
2. **Temporal redundancy**: The same wagon appears in 3-5 consecutive frames
3. **Median filtering**: Suppresses outliers (reflections, noise, extreme blur)
4. **Alignment**: Phase correlation aligns frames for horizontal train motion
5. **No hallucination**: Pure signal processing - no GANs, no invented details

### How It Works
```python
# Sliding window of 3-5 frames
frames = [frame_001, frame_002, frame_003]

# Align frames using phase correlation (horizontal translation)
aligned_frames = align_to_reference(frames)

# Pixel-wise median fusion
fused_frame = np.median(aligned_frames, axis=0)
```

**Result**: Clearer, less noisy wagon numbers for reliable OCR.

---

## 🎛️ Modular Components

Each pipeline stage can be run independently:

### 1. Video to Frames
```bash
python video_to_frames.py train_video.mp4 results/raw_frames 5
```

### 2. Frame Enhancement
```bash
python process_frames.py results/raw_frames weights/gopro_best.pth results/enhanced_frames cuda
```

### 3. Band Extraction
```bash
python extract_bands.py results/enhanced_frames results/band_frames
```

### 4. Temporal Fusion
```bash
python temporal_fusion.py results/band_frames results/fused 3
```

### 5. Text Enhancement
```bash
python text_enhancement.py results/fused results/enhanced_text 2.0 0.3
```

### 6. OCR
```bash
python ocr_pipeline.py results/enhanced_text results/ocr_results easyocr 0.3
```

---

## ⚠️ Failure Cases & Limitations

### When the Pipeline May Fail

1. **Excessive Motion Blur**
   - If ALL frames in a window are extremely blurred
   - **Solution**: Increase FPS or window size to capture clearer frames

2. **Occlusions**
   - Wagon numbers obscured by dirt, graffiti, or objects
   - **Solution**: Manual inspection, multi-angle cameras

3. **Poor Lighting**
   - Very dark scenes where text is invisible
   - **Solution**: Better lighting, infrared cameras

4. **Text Variations**
   - Non-standard fonts, handwritten numbers
   - **Solution**: Fine-tune OCR or use custom recognition models

5. **Alignment Failures**
   - Vertical camera shake can misalign frames
   - **Solution**: More robust alignment (ECC, feature matching)

6. **OCR Confidence**
   - False positives from non-text regions
   - **Solution**: Increase `--confidence` threshold, add validation rules

### Detection Quality Indicators

**High Quality** (Confidence > 0.7):
- Clear, aligned text
- Good contrast
- Multiple detections agree

**Medium Quality** (Confidence 0.3-0.7):
- Partially visible text
- Some blur remains
- May need manual verification

**Low Quality** (Confidence < 0.3):
- Likely false detection
- Severely degraded images
- Reject or manual review

---

## 🛠️ Tuning Parameters

### For Different Scenarios

**High-Speed Trains** (more motion blur):
```bash
--fps 10 --window 5
```
Extract more frames and fuse larger windows

**Low-Light Conditions** (more noise):
```bash
--window 5
```
Larger fusion window suppresses noise better

**Clear Videos** (minimal blur):
```bash
--fps 3 --window 3
```
Fewer frames needed, smaller window

**OCR Fine-Tuning**:
```bash
--confidence 0.5
```
Increase threshold to reduce false positives

---

## 📊 Performance Tips

### GPU Acceleration
- Ensure CUDA is available: `torch.cuda.is_available()`
- Use `--device cuda` for 10-20x speedup

### Memory Management
- If CUDA OOM errors: reduce batch size or use CPU
- Process videos in chunks for very long recordings

### Speed Optimization
- Lower FPS: `--fps 3` (processes fewer frames)
- Smaller window: `--window 3` (faster fusion)
- Use Tesseract OCR (faster than EasyOCR, but less accurate)

---

## 🔍 Validation & Quality Control

### Automatic Validation
The pipeline includes:
- Confidence thresholding
- Wagon number pattern matching (alphanumeric, 4-12 chars)
- Bounding box visualization for manual review

### Manual Verification
Check `6_ocr_results/ocr_visuals/` for:
- Bounding box accuracy
- Text clarity in source images
- Multiple detections per wagon

### Rejection Criteria
Reject detections if:
- Confidence < 0.3
- Text length < 4 or > 12 characters
- No alphanumeric characters
- Multiple conflicting detections

---

## 🧪 Testing

### Test with Sample Video
```bash
# Create a test video from existing frames
ffmpeg -framerate 30 -pattern_type glob -i 'test_sequence/*.png' \
       -c:v libx264 -pix_fmt yuv420p test_video.mp4

# Run pipeline
python run_video_pipeline.py test_video.mp4 weights/gopro_best.pth --output test_results
```

### Verify Each Stage
```bash
# Check frame count
ls results/1_raw_frames/*.png | wc -l

# Visualize crop region
python extract_bands.py results/2_enhanced_frames results/3_band_frames visualize

# Check OCR summary
cat results/6_ocr_results/ocr_results.txt
```

---

## 🤝 Integration

### Use as Python Module
```python
from run_video_pipeline import WagonInspectionPipeline

pipeline = WagonInspectionPipeline(
    video_path='train_video.mp4',
    model_path='weights/gopro_best.pth',
    output_dir='results',
    fps=5,
    window_size=3,
    ocr_engine='easyocr',
    min_confidence=0.3,
    device='cuda'
)

results = pipeline.run()

# Access results
for result in results:
    if result['best_wagon_number']:
        wagon = result['best_wagon_number']
        print(f"Wagon: {wagon['number']} (conf: {wagon['confidence']:.3f})")
```

### Batch Processing
```python
import glob

videos = glob.glob('videos/*.mp4')

for video in videos:
    pipeline = WagonInspectionPipeline(video, 'weights/gopro_best.pth')
    pipeline.run()
```

---

## 📝 Citation & License

Developed for industrial railway wagon inspection systems.  
Uses MIMOUNet deblurring architecture and EasyOCR/Tesseract OCR engines.

**Key Principle**: No hallucination, no GANs - reliable signal processing for safety-critical applications.

---

## 📧 Troubleshooting

**Issue**: `ModuleNotFoundError: No module named 'easyocr'`  
**Solution**: `pip install easyocr`

**Issue**: `CUDA out of memory`  
**Solution**: Use `--device cpu` or reduce video resolution

**Issue**: `No wagon numbers detected`  
**Solution**: 
- Check `5_enhanced_text/` images for text visibility
- Lower `--confidence` threshold
- Increase `--window` size for better fusion

**Issue**: `Tesseract not found`  
**Solution**: Install Tesseract executable from https://github.com/tesseract-ocr/tesseract

**Issue**: Misaligned fused images  
**Solution**: Videos with excessive vertical motion may need better alignment (modify `temporal_fusion.py`)

---

## ✅ Validation Checklist

Before deploying:
- [ ] Test with representative video samples
- [ ] Verify OCR accuracy on ground-truth data
- [ ] Check failure cases and rejection logic
- [ ] Tune confidence thresholds for your use case
- [ ] Validate output format meets requirements
- [ ] Ensure adequate GPU memory for batch processing
- [ ] Set up logging and error handling for production

---

**Happy Wagon Hunting! 🚂**
