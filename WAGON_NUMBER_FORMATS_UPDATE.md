# Wagon Number Format Recognition - Update

## Overview
Updated the OCR pipeline to recognize **multiple wagon number formats** as requested by user, including 8-digit numbers and various alphanumeric combinations.

## What Was Changed
**File Modified:** `ocr_pipeline.py`  
**Method Updated:** `_is_valid_wagon_number()`

## Supported Wagon Number Formats

### ✅ Pattern 1: Pure Digit Numbers (6-10 digits)
- **6 digits:** `123456`
- **7 digits:** `1234567`
- **8 digits:** `12345678` ← **USER REQUESTED**
- **9 digits:** `123456789`
- **10 digits:** `1234567890`

### ✅ Pattern 2: Letters + Digits (1-3 letters + 4-9 digits)
- **1 letter + 6 digits:** `A123456` ← **USER REQUESTED**
- **2 letters + 5 digits:** `AB12345`
- **3 letters + 4 digits:** `ABC1234`
- **1 letter + 7 digits:** `B9876543`

### ✅ Pattern 3: Mixed Alphanumeric
- Must have **both** letters AND digits
- **1-3 letters** maximum
- **3-10 digits** range
- **4-12 total characters**
- Only alphanumeric (no special characters)

## Validation Rules

### What is ACCEPTED ✅
```
12345678        → 8 digits (valid)
A123456         → 1 letter + 6 digits (valid)
AB12345         → 2 letters + 5 digits (valid)
123456789       → 9 digits (valid)
1234567890      → 10 digits (valid)
```

### What is REJECTED ❌
```
12345           → Only 5 digits (too short)
12345678901     → 11 digits (too long)
ABCD1234        → 4 letters (too many letters)
AB12            → Only 2 digits (too few)
HELLO           → No digits
123             → Only 3 digits (too short)
```

## How It Works

### 1. Pre-processing
Text is cleaned before validation:
- Converts to uppercase
- Removes spaces and hyphens
- Example: `"A 123-456"` → `"A123456"`

### 2. Pattern Matching
Three patterns are checked in order:

#### Pattern 1: All Digits
```python
if text.isdigit() and 6 <= len(text) <= 10:
    return True
```
- Accepts: 6, 7, 8, 9, or 10 digit numbers
- Example: `12345678` → ✅ Valid

#### Pattern 2: Letter Prefix + Digits
```python
letter_match = re.match(r'^([A-Z]{1,3})([0-9]{4,9})$', text)
```
- Accepts: 1-3 letters at start, followed by 4-9 digits
- Example: `A123456` → ✅ Valid

#### Pattern 3: Mixed Alphanumeric
```python
if (letter_count >= 1 and letter_count <= 3 and 
    digit_count >= 3 and digit_count <= 10 and
    (letter_count + digit_count) == len(text)):
    return True
```
- Requires BOTH letters and digits
- Max 3 letters, 3-10 digits
- Only alphanumeric characters
- Example: `ABC9876` → ✅ Valid

## Testing Results

All 15 validation tests **PASSED** ✅

```
[OK] PASS | '123456'       → 6 digits
[OK] PASS | '1234567'      → 7 digits
[OK] PASS | '12345678'     → 8 digits - USER REQUESTED ✅
[OK] PASS | '123456789'    → 9 digits
[OK] PASS | '1234567890'   → 10 digits
[OK] PASS | 'A123456'      → 1 letter + 6 digits - USER REQUESTED ✅
[OK] PASS | 'AB12345'      → 2 letters + 5 digits
[OK] PASS | 'ABC1234'      → 3 letters + 4 digits
[OK] PASS | 'B9876543'     → 1 letter + 7 digits
[OK] PASS | '12345'        → Rejected (too short) ✅
[OK] PASS | '12345678901'  → Rejected (too long) ✅
[OK] PASS | 'ABCD1234'     → Rejected (too many letters) ✅
[OK] PASS | 'AB12'         → Rejected (too few digits) ✅
[OK] PASS | 'HELLO'        → Rejected (no digits) ✅
[OK] PASS | '123'          → Rejected (too short) ✅
```

## Integration with OCR Pipeline

### Text Merging
The `_merge_nearby_text()` method combines OCR detections that are close together:
- Merges split detections like `"12345"` + `"678"` → `"12345678"`
- Horizontal distance threshold: 50 pixels
- Vertical alignment tolerance: 30 pixels

### Example Usage in Pipeline
```python
# OCR detects text in wagon image
detections = [
    ("12345", [100, 50]),
    ("678", [200, 52])
]

# Merge nearby text
merged = self._merge_nearby_text(detections)  # → [("12345678", [100, 50])]

# Validate merged wagon number
if self._is_valid_wagon_number("12345678"):
    wagon_numbers.append("12345678")  # ✅ Added to results
```

## How to Use

### 1. Process Wagon Image
```python
from ocr_pipeline import OCRPipeline

ocr = OCRPipeline()
results = ocr.process_wagon_image("wagon.jpg")

print("Detected wagon numbers:", results['wagon_numbers'])
```

### 2. With Wagon Number Enhancer
```python
from wagon_number_enhancer import WagonNumberEnhancer
from ocr_pipeline import OCRPipeline

# Enhance wagon number region
enhancer = WagonNumberEnhancer()
enhanced_img = enhancer.enhance_wagon_number("wagon.jpg")

# Run OCR on enhanced image
ocr = OCRPipeline()
results = ocr.process_wagon_image(enhanced_img)
```

### 3. Test on Single Image
```bash
# Save your wagon image as "uploaded_wagon.jpg"
python test_user_wagon.py
```

## Next Steps

### To Test Your Wagon Image:
1. Save your wagon image as `uploaded_wagon.jpg` in the project directory
2. Run: `python test_user_wagon.py`
3. Check the output for detected wagon numbers

### To Reprocess Videos:
```bash
# Reprocess videos with updated OCR patterns
python test_my_video.py
```

### To View Results:
Open the web dashboard:
```
http://localhost:5000
```

## Key Features

### ✅ Flexible Pattern Matching
- Supports 8-digit wagon numbers (requested)
- Handles alphanumeric combinations (requested)
- Automatically merges split text detections

### ✅ Robust Validation
- Rejects too short/too long numbers
- Rejects too many letters
- Ensures meaningful combinations (both letters + digits for mixed format)

### ✅ Real-world Ready
- Handles spaces and hyphens in input
- Works with both uppercase and lowercase
- Integrated with aggressive wagon number enhancement pipeline

## Technical Details

- **Language:** Python 3.13.5
- **OCR Engine:** EasyOCR (GPU-accelerated)
- **Pattern Matching:** Regular expressions (re module)
- **Image Enhancement:** 7-stage aggressive pipeline with 3x upscaling
- **CUDA Support:** Yes (GPU acceleration for OCR and deblurring)

## Files Modified
1. `ocr_pipeline.py` - Updated `_is_valid_wagon_number()` method
2. `test_wagon_patterns.py` - Created pattern validation tests
3. `test_user_wagon.py` - Created user image testing script

---

**Last Updated:** January 8, 2026  
**Status:** ✅ Fully Tested and Validated (15/15 tests passed)
