# ROI PIPELINE - TESTING & VALIDATION GUIDE

## Overview

This guide provides step-by-step testing procedures to validate the ROI-based inspection pipeline before deployment.

---

## Pre-Test Checklist

- [ ] Python 3.8+ installed
- [ ] All dependencies installed: `pip install ultralytics easyocr opencv-python torch`
- [ ] Test images/videos available
- [ ] Backend directory accessible: `railway_dashboard/backend/`

---

## Test Level 1: Individual Module Testing

### Test 1.1: ROI Detector

**Objective**: Verify YOLO wrapper can detect wagon components.

**Command**:
```bash
cd railway_dashboard/backend
python roi_detector.py test_wagon_image.jpg
```

**Expected Output**:
```
ROI DETECTOR TEST
Model: models/wagon_detector.pt
[WARNING] YOLO model not found, using mock detection

Detected 3 ROIs:
  1. wagon_number - Confidence: 0.85, BBox: [100, 50, 200, 60]
  2. window - Confidence: 0.78, BBox: [150, 150, 180, 200]
  3. door - Confidence: 0.82, BBox: [400, 100, 150, 300]

Mock ROIs saved to: roi_detector_test_output/
```

**Validation**:
- [ ] Script runs without errors
- [ ] 3 mock ROIs detected (if no YOLO model)
- [ ] Output images saved in `roi_detector_test_output/`
- [ ] Cropped ROIs look reasonable

**If using real YOLO model**:
- [ ] Detections match actual wagon components
- [ ] Confidence scores > 0.4
- [ ] Bounding boxes align with components

---

### Test 1.2: ROI Enhancer

**Objective**: Verify task-specific enhancement works correctly.

**Command**:
```bash
python roi_enhancer.py test_wagon_image.jpg
```

**Expected Output**:
```
ROI ENHANCER TEST
Testing enhancement on: test_wagon_image.jpg

Enhanced outputs saved:
  Original: roi_enhancer_test_output/original.jpg
  OCR Enhancement: roi_enhancer_test_output/ocr_enhanced.jpg
  Damage Enhancement: roi_enhancer_test_output/damage_enhanced.jpg
  Global Enhancement: roi_enhancer_test_output/global_enhanced.jpg
```

**Validation**:
- [ ] Script runs without errors
- [ ] 4 output images created
- [ ] OCR enhanced image shows strong contrast (binarized)
- [ ] Damage enhanced image preserves edges (subtle enhancement)
- [ ] Global enhanced image shows light adjustment

**Visual Check**:
- OCR enhancement: Text should be very clear, high contrast
- Damage enhancement: Edges preserved, noise reduced
- No over-enhancement artifacts

---

### Test 1.3: ROI Damage Detector

**Objective**: Verify damage detection algorithms work.

**Command**:
```bash
python roi_damage_detector.py test_wagon_image.jpg
```

**Expected Output**:
```
ROI DAMAGE DETECTOR TEST
Analyzing: test_wagon_image.jpg

DAMAGE ANALYSIS RESULTS:
Sensitivity: medium
Has Damage: True
Damage Type: crack
Confidence: 0.72
Damage Scores:
  - crack: 0.72
  - glass_damage: 0.35
  - deformation: 0.28

Annotated image saved: roi_damage_detector_test_output/annotated.jpg
```

**Validation**:
- [ ] Script runs without errors
- [ ] Damage scores calculated (3 types)
- [ ] Annotated image saved
- [ ] Damage type determined (if any)

**Try different sensitivities**:
```bash
# Edit roi_damage_detector.py, change sensitivity='high'
python roi_damage_detector.py test_wagon_image.jpg
```
- [ ] Higher sensitivity detects more damage
- [ ] Lower sensitivity is more conservative

---

## Test Level 2: Full Pipeline Testing

### Test 2.1: Single Frame Processing

**Objective**: Verify full pipeline processes single frame correctly.

**Create test script** (`test_pipeline_frame.py`):
```python
from roi_inspection_pipeline import ROIInspectionPipeline
import cv2

# Initialize pipeline
pipeline = ROIInspectionPipeline(
    yolo_model_path='models/wagon_detector.pt',
    output_base_dir='test_records',
    use_global_enhancement=False,
    device='cpu'
)

# Read test image
image = cv2.imread('test_wagon_image.jpg')

# Process frame
results = pipeline.process_frame(image, 'test_frame_001')

# Print results
print("\n" + "="*60)
print("FRAME PROCESSING RESULTS")
print("="*60)
print(f"ROI Detections: {results['roi_detections']}")
print(f"Wagon Numbers: {len(results['wagon_numbers'])}")
print(f"Damage Detections: {len(results['damage_detections'])}")

if results['wagon_numbers']:
    print("\nWagon Numbers Found:")
    for wn in results['wagon_numbers']:
        print(f"  - {wn['text']} (Confidence: {wn['confidence']:.2f})")

if results['damage_detections']:
    print("\nDamage Found:")
    for dmg in results['damage_detections']:
        print(f"  - {dmg['damage_type']} on {dmg['roi_class']} "
              f"(Confidence: {dmg['confidence']:.2f})")
```

**Run**:
```bash
python test_pipeline_frame.py
```

**Expected Output**:
```
ROI-BASED INSPECTION PIPELINE INITIALIZATION
...
[PIPELINE] Processing test_frame_001
[STAGE 2] Running YOLO detection...
[STAGE 2] Detected 3 ROIs
[STAGE 3] Processing ROI #1: wagon_number
[OCR] Processing wagon number ROI #0
[MOCK OCR] Simulating OCR...
[OCR] Detected: 'MOCK-000' (confidence: 0.75)
...

FRAME PROCESSING RESULTS
ROI Detections: 3
Wagon Numbers: 1
Damage Detections: 2

Wagon Numbers Found:
  - MOCK-000 (Confidence: 0.75)

Damage Found:
  - crack on window (Confidence: 0.72)
  - glass_damage on door (Confidence: 0.65)
```

**Validation**:
- [ ] Pipeline initializes without errors
- [ ] Frame processing completes
- [ ] ROIs detected (mock or real)
- [ ] Wagon numbers extracted (mock or real OCR)
- [ ] Damage detections found (if applicable)

---

### Test 2.2: Video Processing

**Objective**: Verify pipeline processes entire video.

**Command**:
```bash
python roi_inspection_pipeline.py test_wagon_video.mp4
```

**Expected Output**:
```
VIDEO INSPECTION: inspection_20260104_153025
Video: test_wagon_video.mp4
Video Info: 600 frames @ 30.0 FPS

[PIPELINE] Processing frame_000005
[STAGE 2] Detected 3 ROIs
...
[PROGRESS] 16.7% (100/600 frames)
...
[PROGRESS] 50.0% (300/600 frames)
...
[PROGRESS] 83.3% (500/600 frames)
...

INSPECTION COMPLETE
Frames Processed: 120/600
Wagon Numbers: 15
Damage Detections: 8
Output: test_records/inspection_20260104_153025
```

**Validation**:
- [ ] Video opens successfully
- [ ] Frame sampling works (processes every 5th frame)
- [ ] Progress updates appear
- [ ] Processing completes without crashes
- [ ] Output directory created
- [ ] Metadata JSON saved

**Check Output**:
```bash
ls test_records/inspection_20260104_153025/
```

Expected:
```
wagon_numbers/
damage/
inspection_metadata.json
```

- [ ] `wagon_numbers/` contains cropped wagon number images
- [ ] `damage/` contains annotated damage images
- [ ] `inspection_metadata.json` is valid JSON

**Validate Metadata**:
```bash
cat test_records/inspection_20260104_153025/inspection_metadata.json
```

- [ ] JSON is well-formed
- [ ] Contains `inspection_id`, `video_path`, `total_frames`
- [ ] Contains `wagon_numbers_found` array
- [ ] Contains `damage_detections_found` array
- [ ] Timestamps present (`start_time`, `end_time`)

---

## Test Level 3: Integration Testing

### Test 3.1: Flask API Integration

**Modify `app.py`** to add test endpoint:
```python
from roi_inspection_pipeline import ROIInspectionPipeline

# Initialize pipeline
roi_pipeline = ROIInspectionPipeline(
    output_base_dir='records',
    device='cpu'
)

@app.route('/api/test/roi', methods=['POST'])
def test_roi_pipeline():
    """Test endpoint for ROI pipeline."""
    try:
        data = request.json
        test_image_path = data.get('image_path', 'test_wagon_image.jpg')
        
        # Read image
        import cv2
        image = cv2.imread(test_image_path)
        
        # Process
        results = roi_pipeline.process_frame(image, 'api_test')
        
        return jsonify({
            'success': True,
            'roi_detections': results['roi_detections'],
            'wagon_numbers': results['wagon_numbers'],
            'damage_detections': results['damage_detections']
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

**Start Flask**:
```bash
python app.py
```

**Test with cURL**:
```bash
curl -X POST http://localhost:5000/api/test/roi \
  -H "Content-Type: application/json" \
  -d '{"image_path": "test_wagon_image.jpg"}'
```

**Expected Response**:
```json
{
    "success": true,
    "roi_detections": 3,
    "wagon_numbers": [
        {
            "text": "MOCK-000",
            "confidence": 0.75
        }
    ],
    "damage_detections": [
        {
            "damage_type": "crack",
            "confidence": 0.72,
            "roi_class": "window"
        }
    ]
}
```

**Validation**:
- [ ] Flask starts without errors
- [ ] Endpoint responds (200 OK)
- [ ] JSON response is well-formed
- [ ] Results contain expected fields

---

### Test 3.2: Live Video Integration

**Create test script** (`test_live_roi.py`):
```python
from roi_inspection_pipeline import ROIInspectionPipeline
import cv2

# Initialize pipeline
pipeline = ROIInspectionPipeline(device='cpu')

# Open webcam (or DroidCam)
cap = cv2.VideoCapture(0)  # Change to DroidCam URL if needed

print("Press 'q' to quit, 's' to process frame")

frame_count = 0
while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    frame_count += 1
    
    # Display frame
    cv2.imshow('Live Feed', frame)
    
    key = cv2.waitKey(1) & 0xFF
    
    # Process on 's' press or every 30 frames
    if key == ord('s') or frame_count % 30 == 0:
        print(f"\n[Processing frame {frame_count}]")
        results = pipeline.process_frame(frame, f'live_{frame_count}')
        
        print(f"  Wagon Numbers: {len(results['wagon_numbers'])}")
        print(f"  Damage: {len(results['damage_detections'])}")
    
    if key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
```

**Run**:
```bash
python test_live_roi.py
```

**Validation**:
- [ ] Camera feed opens
- [ ] Frame display works
- [ ] Processing triggered on 's' or every 30 frames
- [ ] Results printed to console
- [ ] No memory leaks (check system monitor)
- [ ] 'q' exits cleanly

---

## Test Level 4: Performance Testing

### Test 4.1: Processing Speed

**Create benchmark script** (`benchmark_roi.py`):
```python
from roi_inspection_pipeline import ROIInspectionPipeline
import cv2
import time

pipeline = ROIInspectionPipeline(device='cpu')

# Test image
image = cv2.imread('test_wagon_image.jpg')

# Warm-up
pipeline.process_frame(image, 'warmup')

# Benchmark
num_iterations = 100
start = time.time()

for i in range(num_iterations):
    results = pipeline.process_frame(image, f'bench_{i}')

end = time.time()
elapsed = end - start
fps = num_iterations / elapsed

print(f"\nBENCHMARK RESULTS")
print(f"{'='*40}")
print(f"Total Time: {elapsed:.2f}s")
print(f"Iterations: {num_iterations}")
print(f"Avg Time/Frame: {elapsed/num_iterations*1000:.2f}ms")
print(f"Processing Speed: {fps:.2f} FPS")
```

**Run**:
```bash
python benchmark_roi.py
```

**Expected Results**:
```
BENCHMARK RESULTS
========================================
Total Time: 20.15s
Iterations: 100
Avg Time/Frame: 201.50ms
Processing Speed: 4.96 FPS
```

**Performance Targets**:
- [ ] CPU mode: > 3 FPS
- [ ] GPU mode: > 15 FPS (if CUDA available)
- [ ] No memory increase over iterations

**If slow**:
- Increase `frame_skip` in pipeline
- Disable `use_global_enhancement`
- Use GPU: `device='cuda'`
- Reduce YOLO confidence threshold (fewer ROIs)

---

### Test 4.2: Memory Usage

**Monitor memory** while processing video:

```bash
# Linux/Mac
python -m memory_profiler roi_inspection_pipeline.py test_video.mp4

# Windows (Task Manager)
# Run pipeline and monitor "Memory" column for python.exe
python roi_inspection_pipeline.py test_video.mp4
```

**Validation**:
- [ ] Memory usage stable (not continuously increasing)
- [ ] Peak memory < 4GB (CPU mode)
- [ ] No memory leaks

---

## Test Level 5: Accuracy Testing

### Test 5.1: OCR Accuracy (with real EasyOCR)

**Prepare test dataset**:
- 10 images with known wagon numbers
- Create ground truth file: `wagon_numbers_gt.txt`
```
image1.jpg,ABC123
image2.jpg,XYZ789
...
```

**Create accuracy test** (`test_ocr_accuracy.py`):
```python
from roi_inspection_pipeline import ROIInspectionPipeline
import cv2

pipeline = ROIInspectionPipeline()

# Read ground truth
with open('wagon_numbers_gt.txt') as f:
    gt_data = [line.strip().split(',') for line in f]

correct = 0
total = len(gt_data)

for image_path, gt_text in gt_data:
    image = cv2.imread(image_path)
    results = pipeline.process_frame(image, image_path)
    
    if results['wagon_numbers']:
        detected_text = results['wagon_numbers'][0]['text']
        if detected_text == gt_text:
            correct += 1
            print(f"✓ {image_path}: {detected_text}")
        else:
            print(f"✗ {image_path}: {detected_text} (GT: {gt_text})")
    else:
        print(f"✗ {image_path}: No detection (GT: {gt_text})")

accuracy = (correct / total) * 100
print(f"\nOCR Accuracy: {accuracy:.1f}% ({correct}/{total})")
```

**Target Accuracy**:
- [ ] > 80% accuracy (good lighting, clear text)
- [ ] > 60% accuracy (varied conditions)

---

### Test 5.2: Damage Detection Accuracy

**Prepare test dataset**:
- 20 images: 10 with damage, 10 without
- Create ground truth: `damage_gt.txt`
```
damaged_window1.jpg,True,crack
damaged_door1.jpg,True,glass_damage
clean_window1.jpg,False,none
...
```

**Create accuracy test** (`test_damage_accuracy.py`):
```python
from roi_inspection_pipeline import ROIInspectionPipeline
import cv2

pipeline = ROIInspectionPipeline()

with open('damage_gt.txt') as f:
    gt_data = [line.strip().split(',') for line in f]

true_positives = 0
true_negatives = 0
false_positives = 0
false_negatives = 0

for image_path, has_damage, damage_type in gt_data:
    has_damage = has_damage == 'True'
    
    image = cv2.imread(image_path)
    results = pipeline.process_frame(image, image_path)
    
    detected = len(results['damage_detections']) > 0
    
    if has_damage and detected:
        true_positives += 1
        print(f"✓ TP: {image_path}")
    elif not has_damage and not detected:
        true_negatives += 1
        print(f"✓ TN: {image_path}")
    elif not has_damage and detected:
        false_positives += 1
        print(f"✗ FP: {image_path}")
    else:
        false_negatives += 1
        print(f"✗ FN: {image_path}")

total = len(gt_data)
accuracy = ((true_positives + true_negatives) / total) * 100

print(f"\nDamage Detection Metrics:")
print(f"  Accuracy: {accuracy:.1f}%")
print(f"  Precision: {true_positives/(true_positives+false_positives)*100:.1f}%")
print(f"  Recall: {true_positives/(true_positives+false_negatives)*100:.1f}%")
```

**Target Metrics**:
- [ ] Accuracy > 70%
- [ ] Low false positive rate (< 20%)
- [ ] Reasonable recall (> 60%)

---

## Troubleshooting

### Issue: ImportError for ultralytics
**Solution**: `pip install ultralytics`

### Issue: CUDA out of memory
**Solution**: Use CPU mode or reduce batch size
```python
pipeline = ROIInspectionPipeline(device='cpu')
```

### Issue: No ROIs detected
**Solutions**:
1. Lower confidence threshold in `roi_detector.py`
2. Check if YOLO model is trained properly
3. Verify input image quality

### Issue: OCR returns gibberish
**Solutions**:
1. Check enhancement quality (may be too aggressive)
2. Verify EasyOCR language setting
3. Try different OCR engines

### Issue: High false positive damage rate
**Solutions**:
1. Lower damage sensitivity: `ROIDamageDetector(sensitivity='low')`
2. Adjust thresholds in `roi_damage_detector.py`
3. Use better quality images for training

---

## Test Summary Checklist

### Module Tests
- [ ] ROI Detector works (mock or real YOLO)
- [ ] ROI Enhancer produces correct outputs
- [ ] ROI Damage Detector analyzes damage

### Pipeline Tests
- [ ] Single frame processing works
- [ ] Video processing completes successfully
- [ ] Output structure is correct

### Integration Tests
- [ ] Flask API endpoint works
- [ ] Live video processing works

### Performance Tests
- [ ] Processing speed meets targets
- [ ] Memory usage is stable

### Accuracy Tests
- [ ] OCR accuracy acceptable (if real OCR)
- [ ] Damage detection metrics acceptable

---

## Sign-Off

**Tested By**: _______________  
**Date**: _______________  
**System**: _______________  
**Status**: [ ] PASS  [ ] FAIL  

**Notes**:
```
[Add any observations, issues, or recommendations]
```

---

**END OF TESTING GUIDE**
