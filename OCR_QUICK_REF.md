# OCR Quick Reference Card

## 🚀 Quick Commands

### Test OCR on Existing Fusion Results
```bash
python quick_ocr_test.py
```

### Run Complete Pipeline (Fusion + OCR)
```bash
python run_full_pipeline_with_ocr.py
```

### Debug OCR Issues
```bash
python debug_ocr.py my_fusion_results/final_ocr_input.png
```

### Standalone OCR
```bash
# EasyOCR (more accurate)
python run_ocr_wagon.py --input image.png --confidence 0.4

# Tesseract (faster)
python run_ocr_tesseract.py --input image.png --confidence 40
```

---

## 📁 Key Files

| File | Purpose |
|------|---------|
| `run_ocr_wagon.py` | Main OCR (EasyOCR) |
| `run_ocr_tesseract.py` | Alternative OCR (Tesseract) |
| `run_full_pipeline_with_ocr.py` | Fusion + OCR combined |
| `quick_ocr_test.py` | Quick testing tool |
| `debug_ocr.py` | Debugging & visualization |
| `production_integration_example.py` | Production code template |
| `OCR_IMPLEMENTATION_GUIDE.md` | Complete documentation |
| `OCR_SUMMARY.md` | Implementation summary |

---

## 🎯 Expected Output

### Success Case
```
FINAL RESULT
--------------------------------------------------
  Wagon Number: SW456789
  Confidence:   0.873
  Status:       READABLE
```

### Rejection Case
```
FINAL RESULT
--------------------------------------------------
  Wagon Number: UNREADABLE
  Confidence:   0.234
  Status:       UNREADABLE
```

---

## ⚙️ Configuration

### Adjust Confidence Threshold
```bash
# More strict (fewer false positives)
--confidence 0.6

# More lenient (fewer rejections)
--confidence 0.3

# Default (recommended)
--confidence 0.4
```

### Choose OCR Engine

**EasyOCR** (Recommended):
- ✅ More accurate
- ✅ Better with complex fonts
- ⚠️ Slower initialization
- ⚠️ Larger memory footprint

**Tesseract** (Alternative):
- ✅ Faster
- ✅ Lighter dependencies
- ⚠️ Less accurate on complex text
- ⚠️ Requires separate binary install

---

## 🔧 Common Issues

### "No module named 'easyocr'"
```bash
pip install easyocr
```

### "Tesseract not found"
Download from: https://github.com/UB-Mannheim/tesseract/wiki
```bash
pip install pytesseract
```

### "No text detected"
1. Check image quality with: `python debug_ocr.py image.png`
2. Try different preprocessing approaches
3. Lower confidence threshold (testing only)
4. Try both EasyOCR and Tesseract

### "CUDA out of memory"
Edit OCR script, set `gpu=False`:
```python
self.reader = easyocr.Reader(languages, gpu=False)
```

---

## 📊 Validation Patterns

Current patterns (edit in `validate_wagon_number()` method):

```regex
# Pattern 1: Optional 2-letter prefix + 6-9 digits
^[A-Z]{0,2}\d{6,9}$
Examples: SW123456, EC987654, 123456789

# Pattern 2: Pure numeric, 6-10 digits
^\d{6,10}$
Examples: 123456, 1234567890
```

---

## 🎓 Integration Example

```python
from temporal_fusion_wagon import TemporalFusionPipeline
from run_ocr_wagon import WagonNumberOCR

# Initialize
fusion = TemporalFusionPipeline(weights_path='weights/gopro_best.pth')
ocr = WagonNumberOCR(confidence_threshold=0.4)

# Process
fusion.process_sequence(frames, output_dir='results/')
result = ocr.extract_wagon_number('results/final_ocr_input.png', 'results/')

# Use
if result['wagon_number'] != 'UNREADABLE':
    print(f"Wagon: {result['wagon_number']}")
else:
    print("Manual inspection required")
```

---

## 📈 Quality Grades

| Grade | Score | Meaning |
|-------|-------|---------|
| A | 9-10 | Excellent - High confidence, clear read |
| B | 7-8.9 | Good - Readable with decent confidence |
| C | 5-6.9 | Fair - Readable but low confidence |
| D | 3-4.9 | Poor - Questionable result |
| F | 0-2.9 | Fail - Unreadable or very low confidence |

---

## ✅ Safety Checklist

- [x] No hallucination of missing digits
- [x] Confidence-based rejection
- [x] Pattern validation
- [x] Explicit "UNREADABLE" status
- [x] Traceable confidence scores
- [x] Visual verification outputs
- [x] Metadata logging

---

## 📞 Getting Help

1. Check `OCR_IMPLEMENTATION_GUIDE.md` for details
2. Run `debug_ocr.py` to diagnose issues
3. Review `OCR_SUMMARY.md` for overview
4. Check example in `production_integration_example.py`

---

## 🎯 Remember

**This is a safety-critical system.**

✅ Better to reject than guess
✅ "UNREADABLE" is a valid result
✅ Confidence scores matter
✅ Pattern validation prevents errors
✅ Manual review is part of the process

**False negative (reject good) > False positive (accept bad)**
