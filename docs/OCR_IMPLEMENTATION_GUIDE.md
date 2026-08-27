# Wagon Number OCR - Implementation Guide

## Overview

This OCR system extracts wagon numbers from temporally-fused railway wagon images. It implements **safety-critical validation** to ensure:
- ✅ High-confidence extractions are accepted
- ❌ Low-confidence or invalid results are rejected as "UNREADABLE"
- 🚫 No hallucination or guessing of missing digits

---

## Files Created

### 1. `run_ocr_wagon.py` (EasyOCR version)
- **Purpose**: Extract wagon numbers using EasyOCR (GPU-accelerated, multi-language)
- **Pros**: More accurate, works better with complex text
- **Cons**: Slower initialization (downloads models), heavier dependencies

### 2. `run_ocr_tesseract.py` (Tesseract version)
- **Purpose**: Extract wagon numbers using Tesseract OCR (lightweight, fast)
- **Pros**: Faster, simpler dependencies, well-established
- **Cons**: May be less accurate on challenging text

### 3. `run_full_pipeline_with_ocr.py`
- **Purpose**: Complete pipeline combining temporal fusion + OCR
- **Usage**: Interactive GUI to select frames and run end-to-end

---

## Installation

### Option 1: EasyOCR (Recommended for Accuracy)

```bash
pip install easyocr opencv-python numpy pillow
```

**First run will download models (~100MB). This is normal.**

### Option 2: Tesseract OCR (Recommended for Speed)

```bash
# Install Python package
pip install pytesseract opencv-python numpy pillow

# Install Tesseract binary (Windows)
# Download from: https://github.com/UB-Mannheim/tesseract/wiki
# Install and add to PATH
```

---

## Usage

### Quick Test: OCR on Existing Results

If you already have fusion results in `my_fusion_results/`:

```bash
# Using EasyOCR
python run_ocr_wagon.py

# Using Tesseract
python run_ocr_tesseract.py

# Custom input/output
python run_ocr_wagon.py --input path/to/image.png --output-dir results/ --confidence 0.5
```

### Complete Pipeline: Fusion + OCR

Run the full workflow interactively:

```bash
python run_full_pipeline_with_ocr.py
```

This will:
1. Prompt you to select 3-5 consecutive frames
2. Run temporal fusion to reduce blur
3. Extract wagon number via OCR
4. Save all results with visualizations

---

## How It Works

### Pipeline Flow

```
Input Frames
    ↓
[Temporal Fusion]  ← Deblur + align + fuse
    ↓
final_ocr_input.png
    ↓
[Preprocessing]    ← Grayscale + threshold + denoise
    ↓
[OCR Engine]       ← EasyOCR or Tesseract
    ↓
[Validation]       ← Pattern matching + confidence check
    ↓
Wagon Number (or "UNREADABLE")
```

### Preprocessing Steps

Before OCR, the image undergoes:

1. **Grayscale Conversion**
   - Converts RGB/BGR to single-channel grayscale

2. **Adaptive Thresholding**
   - Handles varying lighting conditions
   - Creates binary (black/white) image for clearer text

3. **Noise Removal**
   - Removes small contours and artifacts
   - Uses morphological operations to clean image

4. **Aspect Ratio Preservation**
   - No resizing or distortion
   - Maintains original text proportions

### Validation Logic

Extracted text must pass TWO tests:

#### Test 1: Pattern Matching

Valid wagon number formats:
- **Pure numeric**: 6-10 digits (e.g., `123456`, `1234567890`)
- **With prefix**: 2 letters + 6-9 digits (e.g., `SW123456`, `EC987654321`)

Invalid examples:
- Too short: `12345` (< 6 chars)
- Too long: `123456789012` (> 11 chars)
- Invalid format: `ABC123` (3 letters)
- Special chars: `SW-123456` (hyphen not allowed in final output)

#### Test 2: Confidence Threshold

- **EasyOCR**: Default threshold = 0.4 (scale: 0.0-1.0)
- **Tesseract**: Default threshold = 40% (scale: 0-100)

If average confidence < threshold → **REJECTED as "UNREADABLE"**

---

## Output Files

After running OCR, you'll find:

### In the output directory:

1. **`ocr_visualization.png`**
   - Original image with bounding boxes drawn
   - Green boxes = high confidence
   - Red boxes = low confidence
   - Final result displayed at top

2. **`ocr_preprocessed.png`**
   - The preprocessed image sent to OCR
   - Useful for debugging OCR failures

3. **`final_ocr_input.png`**
   - Enhanced fused image (from temporal fusion)
   - Input to the OCR system

---

## Configuration

### Confidence Threshold

Adjust based on your requirements:

```bash
# More strict (fewer false positives, more rejections)
python run_ocr_wagon.py --confidence 0.6

# More lenient (fewer rejections, risk of false positives)
python run_ocr_wagon.py --confidence 0.3
```

**Recommended**: 0.4 for EasyOCR, 40 for Tesseract

### OCR Engine Selection

**Use EasyOCR when**:
- Maximum accuracy is critical
- GPU is available
- Text has complex fonts or orientations
- Multi-language support needed

**Use Tesseract when**:
- Speed is important
- Simpler deployment (lightweight)
- Standard fonts with clear text
- CPU-only environment

---

## Safety Features

### 1. No Hallucination
The system will **never** guess or fill in missing digits. If OCR can't read the text confidently, it returns `"UNREADABLE"`.

### 2. Pattern Validation
Even if OCR returns text with high confidence, it's rejected if it doesn't match expected wagon number patterns.

### 3. Explicit Rejection
Results are clearly marked as:
- ✅ `READABLE` with the extracted number
- ❌ `UNREADABLE` (no partial/uncertain output)

### 4. Confidence Reporting
Every result includes confidence score for traceability and quality monitoring.

---

## Troubleshooting

### "No module named 'easyocr'"
```bash
pip install easyocr
```

### "Tesseract is not installed"
Download and install from: https://github.com/UB-Mannheim/tesseract/wiki

Add Tesseract to PATH or specify location:
```python
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

### "CUDA out of memory" (EasyOCR)
EasyOCR tries to use GPU by default. If you get CUDA errors:

1. Use CPU mode (slower but works):
   Edit `run_ocr_wagon.py`, line 30:
   ```python
   self.reader = easyocr.Reader(languages, gpu=False)  # Changed to False
   ```

2. Or use Tesseract instead (CPU-only by default)

### OCR Returns "UNREADABLE" for Clear Text

Possible causes:
1. **Low confidence**: Try lowering threshold
   ```bash
   python run_ocr_wagon.py --confidence 0.3
   ```

2. **Pattern mismatch**: Check if your wagon numbers follow expected formats
   - Modify `validate_wagon_number()` method to match your patterns

3. **Poor preprocessing**: The adaptive thresholding might not work well
   - Try adjusting `blockSize` and `C` parameters in `preprocess_for_ocr()`

---

## Advanced Customization

### Modify Wagon Number Patterns

Edit the `validate_wagon_number()` method in either OCR script:

```python
def validate_wagon_number(self, text):
    normalized = re.sub(r'[^A-Z0-9]', '', text.upper())
    
    # YOUR CUSTOM PATTERN HERE
    # Example: Exactly 8 digits
    pattern = r'^\d{8}$'
    
    if re.match(pattern, normalized):
        return True, normalized
    
    return False, normalized
```

### Adjust Preprocessing

Edit `preprocess_for_ocr()` method:

```python
# Try different thresholding methods
binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

# Or try inversion if text is white-on-black
binary = cv2.bitwise_not(binary)

# Stronger noise removal
kernel = np.ones((3, 3), np.uint8)
cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
```

---

## Performance Notes

### EasyOCR
- **First run**: 30-60 seconds (downloads models)
- **Subsequent runs**: 3-5 seconds per image
- **Memory**: ~2GB GPU / 4GB RAM

### Tesseract
- **All runs**: 1-2 seconds per image
- **Memory**: ~500MB RAM

---

## Integration with Existing Code

The OCR system is designed to work seamlessly with your temporal fusion pipeline:

```python
from temporal_fusion_wagon import TemporalFusionPipeline
from run_ocr_wagon import WagonNumberOCR

# 1. Run fusion
pipeline = TemporalFusionPipeline(weights_path='weights/gopro_best.pth')
pipeline.process_sequence(frames, output_dir='results/')

# 2. Run OCR
ocr = WagonNumberOCR(confidence_threshold=0.4)
result = ocr.extract_wagon_number('results/final_ocr_input.png', 'results/')

# 3. Use result
if result['wagon_number'] != 'UNREADABLE':
    print(f"✓ Wagon number: {result['wagon_number']}")
    print(f"  Confidence: {result['confidence']:.3f}")
else:
    print("⚠ Could not read wagon number")
```

---

## Example Output

```
======================================================================
WAGON NUMBER OCR EXTRACTION
======================================================================
Input: my_fusion_results/final_ocr_input.png
Size: 1920×180 px

Step 1: Preprocessing for OCR
----------------------------------------------------------------------
  ✓ Grayscale conversion
  ✓ Adaptive thresholding
  ✓ Noise removal

Step 2: Running EasyOCR
----------------------------------------------------------------------
  Detected 2 text region(s)

Step 3: Processing Detections
----------------------------------------------------------------------
  [1] Text: 'SW' | Confidence: 0.892
  [2] Text: '456789' | Confidence: 0.854

Step 4: Validation
----------------------------------------------------------------------
  Combined text: 'SW456789'
  Normalized: 'SW456789'
  Average confidence: 0.873
  Confidence threshold: 0.400
  Pattern valid: True

  ✓ ACCEPTED: 'SW456789'

Step 5: Creating Visualization
----------------------------------------------------------------------
  ✓ Saved: my_fusion_results/ocr_visualization.png

======================================================================
FINAL RESULT
======================================================================

  Wagon Number: SW456789
  Confidence:   0.873
  Status:       READABLE

======================================================================
```

---

## Next Steps

1. **Test on your images**: Run `python run_ocr_wagon.py` or `python run_full_pipeline_with_ocr.py`

2. **Tune threshold**: Adjust confidence threshold based on your accuracy requirements

3. **Customize patterns**: Modify validation logic to match your specific wagon number formats

4. **Integrate**: Use the OCR classes in your larger inspection system

5. **Monitor**: Track confidence scores and rejection rates to improve preprocessing

---

## Contact & Support

For issues related to:
- **EasyOCR**: https://github.com/JaidedAI/EasyOCR
- **Tesseract**: https://github.com/tesseract-ocr/tesseract
- **OpenCV**: https://opencv.org/

---

**Remember**: This is a safety-critical system. It's designed to reject uncertain results rather than guess. This is the correct behavior for railway inspection applications.
