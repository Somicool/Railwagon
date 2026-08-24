# ROI-BASED INSPECTION PIPELINE ARCHITECTURE

## Executive Summary

This document describes the **Region-of-Interest (ROI) Based Inspection Pipeline** for railway wagon inspection. The pipeline uses YOLOv8 object detection to identify specific wagon components (wagon numbers, windows, doors) and applies task-specific processing strategies to each detected region.

**Key Innovation**: Instead of processing the entire frame with aggressive enhancement (which degrades quality), we:
1. Detect specific regions of interest (ROIs)
2. Apply task-appropriate enhancement to each ROI individually
3. Perform specialized analysis (OCR for text, damage detection for structures)

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                       INPUT FRAME (Video/Image)                       │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
              ┌────────────────────────────────┐
              │   OPTIONAL: Global Enhancement │ (Light only)
              │   - Mild contrast adjustment   │
              │   - Slight denoising           │
              └────────────┬───────────────────┘
                           │
                           ▼
              ┌────────────────────────────────┐
              │    STAGE 1: ROI DETECTION      │
              │    YOLOv8 Object Detection     │
              │                                │
              │  Classes:                      │
              │    - wagon_number              │
              │    - window                    │
              │    - door                      │
              └────────────┬───────────────────┘
                           │
                           ▼
         ┌─────────────────┴─────────────────┐
         │                                   │
         ▼                                   ▼
┌────────────────────┐            ┌────────────────────┐
│  wagon_number ROI  │            │  window/door ROI   │
└─────────┬──────────┘            └─────────┬──────────┘
          │                                 │
          ▼                                 ▼
┌────────────────────┐            ┌────────────────────┐
│  STAGE 2A:         │            │  STAGE 2B:         │
│  Aggressive        │            │  Mild              │
│  Text Enhancement  │            │  Structural        │
│                    │            │  Enhancement       │
│  • Denoise         │            │                    │
│  • CLAHE           │            │  • Bilateral       │
│  • Sharpen         │            │    filter          │
│  • Adaptive        │            │  • Light contrast  │
│    threshold       │            │  • Slight sharpen  │
│  • Morphology      │            │                    │
└─────────┬──────────┘            └─────────┬──────────┘
          │                                 │
          ▼                                 ▼
┌────────────────────┐            ┌────────────────────┐
│  STAGE 3A:         │            │  STAGE 3B:         │
│  OCR PROCESSING    │            │  DAMAGE DETECTION  │
│                    │            │                    │
│  • EasyOCR         │            │  • Crack detection │
│  • Text extraction │            │  • Glass damage    │
│  • Confidence      │            │  • Deformation     │
│    scoring         │            │  • Confidence      │
│                    │            │    scoring         │
└─────────┬──────────┘            └─────────┬──────────┘
          │                                 │
          └─────────────────┬───────────────┘
                            │
                            ▼
                ┌────────────────────────┐
                │  STAGE 4: AGGREGATION  │
                │                        │
                │  • Merge results       │
                │  • Save ROI crops      │
                │  • Generate metadata   │
                │  • Create annotations  │
                └────────────┬───────────┘
                             │
                             ▼
                ┌────────────────────────┐
                │   OUTPUT STRUCTURE     │
                │                        │
                │  records/              │
                │    └─ inspection_id/   │
                │       ├─ wagon_numbers/│
                │       ├─ damage/       │
                │       └─ metadata.json │
                └────────────────────────┘
```

---

## Modular Components

### 1. ROI Detector (`roi_detector.py`)

**Purpose**: Wraps YOLOv8 for detecting wagon components.

**Input**: Video frame (BGR numpy array)

**Output**: List of detections
```python
[
    {
        'class': 'wagon_number',
        'bbox': [x, y, w, h],
        'confidence': 0.92,
        'crop': np.ndarray  # Cropped ROI image
    },
    {
        'class': 'window',
        'bbox': [x, y, w, h],
        'confidence': 0.87,
        'crop': np.ndarray
    },
    ...
]
```

**Key Features**:
- YOLOv8 wrapper with confidence thresholding
- Automatic ROI cropping
- Mock detection fallback when model unavailable
- GPU/CPU support

**Pseudocode**:
```python
def detect_rois(frame):
    results = yolo_model.predict(frame)
    detections = []
    
    for detection in results:
        class_name = detection.class_name
        bbox = detection.bounding_box
        confidence = detection.confidence
        
        if confidence > threshold:
            crop = frame[bbox.y:bbox.y+bbox.h, bbox.x:bbox.x+bbox.w]
            detections.append({
                'class': class_name,
                'bbox': [bbox.x, bbox.y, bbox.w, bbox.h],
                'confidence': confidence,
                'crop': crop
            })
    
    return detections
```

---

### 2. ROI Enhancer (`roi_enhancer.py`)

**Purpose**: Apply task-specific enhancement to detected ROIs.

**Enhancement Strategies**:

#### A. Aggressive Enhancement (for OCR)
```
Input ROI → Denoise → CLAHE → Sharpen → Adaptive Threshold → Morphology → Enhanced ROI
```

**Pipeline Steps**:
1. **Denoise**: Bilateral filter (preserves edges)
2. **CLAHE**: Contrast Limited Adaptive Histogram Equalization
3. **Sharpen**: Unsharp mask
4. **Adaptive Threshold**: Binarization for text
5. **Morphology**: Close small gaps, remove noise

#### B. Mild Enhancement (for Damage Detection)
```
Input ROI → Bilateral Filter → Light Contrast → Slight Sharpen → Enhanced ROI
```

**Pipeline Steps**:
1. **Bilateral Filter**: Noise reduction with edge preservation
2. **Light Contrast**: Subtle CLAHE (clip_limit=1.5)
3. **Slight Sharpen**: Gentle kernel

**Pseudocode**:
```python
def enhance_roi(roi_crop, roi_class):
    if roi_class == 'wagon_number':
        # AGGRESSIVE enhancement for OCR
        enhanced = denoise(roi_crop)
        enhanced = clahe(enhanced, clip_limit=3.0)
        enhanced = sharpen(enhanced)
        enhanced = adaptive_threshold(enhanced)
        enhanced = morphology_close(enhanced)
        
    elif roi_class in ['window', 'door']:
        # MILD enhancement for damage detection
        enhanced = bilateral_filter(roi_crop)
        enhanced = clahe(enhanced, clip_limit=1.5)
        enhanced = slight_sharpen(enhanced)
    
    return enhanced
```

---

### 3. ROI Damage Detector (`roi_damage_detector.py`)

**Purpose**: Analyze window/door ROIs for structural damage.

**Detection Methods**:

#### A. Crack Detection
- Edge detection (Canny)
- Contour analysis for elongated shapes
- Variance threshold

#### B. Glass Damage Detection
- Laplacian variance (sharpness)
- Bright spot detection (glass fragments)
- Circularity analysis

#### C. Deformation Detection
- Contour irregularity
- Circularity measurement
- Aspect ratio analysis

**Output Format**:
```python
{
    'has_damage': True,
    'damage_type': 'crack',  # or 'glass_damage', 'deformation', 'multiple'
    'confidence': 0.87,
    'damage_score': {
        'crack': 0.87,
        'glass_damage': 0.23,
        'deformation': 0.15
    },
    'details': {
        'crack_variance': 1250.5,
        'glass_laplacian': 45.2,
        'deformation_circularity': 0.65
    }
}
```

**Pseudocode**:
```python
def analyze_damage(roi_crop, roi_class):
    scores = {}
    
    # Crack detection
    edges = canny(roi_crop)
    contours = find_contours(edges)
    elongated_contours = filter_by_aspect_ratio(contours, min_ratio=3.0)
    crack_variance = compute_variance(elongated_contours)
    scores['crack'] = crack_variance
    
    # Glass damage detection
    laplacian_var = laplacian_variance(roi_crop)
    bright_spots = detect_bright_regions(roi_crop)
    scores['glass_damage'] = (laplacian_var + bright_spots) / 2
    
    # Deformation detection
    irregularity = measure_circularity(contours)
    scores['deformation'] = irregularity
    
    # Determine primary damage type
    max_score = max(scores.values())
    if max_score > threshold:
        damage_type = key_with_max_score(scores)
        return {
            'has_damage': True,
            'damage_type': damage_type,
            'confidence': normalize(max_score),
            'damage_score': scores
        }
    else:
        return {'has_damage': False}
```

---

### 4. ROI Inspection Pipeline (`roi_inspection_pipeline.py`)

**Purpose**: Orchestrate entire inspection workflow.

**Main Pipeline Flow**:

```python
def process_frame(frame):
    # STAGE 1: Optional global enhancement
    if use_global_enhancement:
        frame = global_enhancer.enhance_frame(frame)
    
    # STAGE 2: ROI detection
    detections = roi_detector.detect_rois(frame)
    
    results = {
        'wagon_numbers': [],
        'damage_detections': []
    }
    
    # STAGE 3: Process each ROI
    for detection in detections:
        roi_class = detection['class']
        roi_crop = detection['crop']
        
        # Task-specific enhancement
        enhanced_roi = roi_enhancer.enhance_roi(roi_crop, roi_class)
        
        # Task-specific processing
        if roi_class == 'wagon_number':
            # OCR processing
            ocr_result = run_ocr(enhanced_roi)
            results['wagon_numbers'].append(ocr_result)
            
        elif roi_class in ['window', 'door']:
            # Damage detection
            damage_result = damage_detector.analyze_damage(enhanced_roi, roi_class)
            if damage_result['has_damage']:
                results['damage_detections'].append(damage_result)
    
    return results
```

**Video Processing**:
```python
def process_video(video_path, inspection_id):
    cap = cv2.VideoCapture(video_path)
    
    inspection_results = {
        'wagon_numbers_found': [],
        'damage_detections_found': []
    }
    
    frame_count = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        frame_count += 1
        
        # Process frame
        results = process_frame(frame)
        
        # Save wagon number crops
        for wn in results['wagon_numbers']:
            save_crop(wn, f"wagon_numbers/wagon_{wn['text']}_{frame_count}.jpg")
            inspection_results['wagon_numbers_found'].append(wn)
        
        # Save damage crops
        for dmg in results['damage_detections']:
            save_crop(dmg, f"damage/damage_{dmg['type']}_{frame_count}.jpg")
            inspection_results['damage_detections_found'].append(dmg)
    
    # Save metadata
    save_json(inspection_results, f"{inspection_id}/metadata.json")
    
    return inspection_results
```

---

## Output Structure

```
records/
├─ inspection_20260104_143052/
│  ├─ wagon_numbers/
│  │  ├─ wagon_ABC123_000150.jpg
│  │  ├─ wagon_XYZ789_000320.jpg
│  │  └─ ...
│  ├─ damage/
│  │  ├─ damage_crack_000180.jpg
│  │  ├─ damage_glass_damage_000245.jpg
│  │  └─ ...
│  └─ inspection_metadata.json
│
├─ inspection_20260104_150223/
│  └─ ...
```

**Metadata Format** (`inspection_metadata.json`):
```json
{
    "inspection_id": "inspection_20260104_143052",
    "video_path": "videos/wagon_inspection_01.mp4",
    "total_frames": 1200,
    "frames_processed": 240,
    "wagon_numbers_found": [
        {
            "text": "ABC123",
            "confidence": 0.92,
            "frame": 150,
            "path": "inspection_20260104_143052/wagon_numbers/wagon_ABC123_000150.jpg"
        }
    ],
    "damage_detections_found": [
        {
            "damage_type": "crack",
            "confidence": 0.87,
            "roi_class": "window",
            "frame": 180,
            "path": "inspection_20260104_143052/damage/damage_crack_000180.jpg"
        }
    ],
    "start_time": "2026-01-04T14:30:52",
    "end_time": "2026-01-04T14:35:18"
}
```

---

## Integration with Existing System

### Current System (inspection_processor.py)

The existing system has:
- `run_live_inspection()` - Live camera feed processing
- `run_recorded_inspection()` - Recorded video processing
- `process_single_image()` - Single image processing

### Integration Strategy

**Option 1: Replace Full-Frame Processing**
```python
# OLD (Full-frame processing)
def run_recorded_inspection(video_path):
    cap = cv2.VideoCapture(video_path)
    while cap.isOpened():
        ret, frame = cap.read()
        # ... apply deblurring to entire frame
        # ... run OCR on entire frame
        # ... run damage detection on entire frame

# NEW (ROI-based processing)
def run_recorded_inspection(video_path):
    pipeline = ROIInspectionPipeline()
    results = pipeline.process_video(video_path)
    return results
```

**Option 2: Hybrid Approach (Toggle)**
```python
def run_recorded_inspection(video_path, use_roi_pipeline=True):
    if use_roi_pipeline:
        # Use new ROI-based pipeline
        pipeline = ROIInspectionPipeline()
        return pipeline.process_video(video_path)
    else:
        # Use legacy full-frame processing
        return legacy_full_frame_processing(video_path)
```

### Flask API Integration

**New Endpoint**:
```python
@app.route('/api/inspect/roi', methods=['POST'])
def inspect_roi():
    video_path = request.json.get('video_path')
    
    pipeline = ROIInspectionPipeline()
    results = pipeline.process_video(video_path)
    
    return jsonify(results)
```

**Modify Existing Endpoints**:
```python
@app.route('/api/inspect/recorded', methods=['POST'])
def inspect_recorded():
    video_path = request.json.get('video_path')
    use_roi = request.json.get('use_roi_pipeline', True)
    
    if use_roi:
        pipeline = ROIInspectionPipeline()
        results = pipeline.process_video(video_path)
    else:
        results = legacy_inspection(video_path)
    
    return jsonify(results)
```

---

## Performance Optimization

### 1. Frame Sampling
Process every Nth frame instead of all frames:
```python
frame_skip = 5  # Process every 5th frame
if frame_count % frame_skip == 0:
    results = pipeline.process_frame(frame)
```

### 2. GPU Acceleration
Use CUDA for YOLO and OCR:
```python
pipeline = ROIInspectionPipeline(device='cuda')
```

### 3. Batch Processing
Process multiple ROIs in parallel:
```python
enhanced_rois = [roi_enhancer.enhance_roi(roi['crop'], roi['class']) 
                 for roi in detections]
```

### 4. Caching
Cache OCR reader and YOLO model (lazy loading):
```python
if self.ocr_reader is None:
    self.ocr_reader = easyocr.Reader(['en'])
```

---

## Deployment Checklist

- [ ] Train YOLOv8 model on wagon dataset (wagon_number, window, door)
- [ ] Save trained model to `models/wagon_detector.pt`
- [ ] Install dependencies: `pip install ultralytics easyocr opencv-python`
- [ ] Test individual modules:
  ```bash
  python roi_detector.py test_image.jpg
  python roi_enhancer.py test_image.jpg
  python roi_damage_detector.py test_image.jpg
  ```
- [ ] Test full pipeline:
  ```bash
  python roi_inspection_pipeline.py test_video.mp4
  ```
- [ ] Integrate with Flask backend
- [ ] Update frontend to display ROI-based results
- [ ] Performance testing on target hardware

---

## Advantages Over Full-Frame Processing

| Aspect | Full-Frame Processing | ROI-Based Processing |
|--------|----------------------|----------------------|
| **Enhancement Quality** | Aggressive enhancement degrades non-text regions | Task-specific enhancement preserves quality |
| **Processing Speed** | Process entire frame | Process only detected regions |
| **Accuracy** | OCR struggles with noisy backgrounds | OCR focused on text-only regions |
| **Damage Detection** | False positives from background noise | Focused on actual windows/doors |
| **Modularity** | Tightly coupled components | Swappable modules (detector, enhancer, analyzer) |
| **Scalability** | Resource-intensive | Efficient, can process higher resolution |

---

## Troubleshooting

### YOLO Model Not Found
```python
# Pipeline falls back to mock detection
[WARNING] YOLO model not found, using mock detection
```
**Solution**: Train YOLOv8 model or provide path to pre-trained model

### OCR Not Installed
```python
[WARNING] easyocr not installed. OCR will be simulated.
```
**Solution**: `pip install easyocr`

### CUDA Out of Memory
```python
[ERROR] CUDA out of memory
```
**Solution**: Switch to CPU mode or reduce batch size
```python
pipeline = ROIInspectionPipeline(device='cpu')
```

### No ROIs Detected
```python
[PIPELINE] No ROIs detected
```
**Solution**: 
- Lower YOLO confidence threshold
- Check if model is trained on correct classes
- Verify input image quality

---

## License & Credits

**Author**: Railway Wagon Inspection System  
**Date**: January 4, 2026  
**Framework**: YOLOv8 (Ultralytics), EasyOCR, OpenCV  
**Purpose**: Hackathon Demo - Industrial Railway Inspection

---

**END OF ARCHITECTURE DOCUMENT**
