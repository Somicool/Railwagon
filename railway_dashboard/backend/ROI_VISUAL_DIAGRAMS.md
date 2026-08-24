# ROI PIPELINE - VISUAL DIAGRAMS

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│                         RAILWAY INSPECTION SYSTEM                           │
│                                                                             │
│  ┌───────────────┐   ┌──────────────┐   ┌──────────────┐                  │
│  │  Live Camera  │   │ Recorded     │   │ Single       │                  │
│  │  (DroidCam)   │   │ Video Upload │   │ Image Upload │                  │
│  └───────┬───────┘   └──────┬───────┘   └──────┬───────┘                  │
│          │                  │                  │                           │
│          └──────────────────┴──────────────────┘                           │
│                             │                                              │
│                             ▼                                              │
│              ┌──────────────────────────────┐                              │
│              │                              │                              │
│              │   ROI INSPECTION PIPELINE    │                              │
│              │   (roi_inspection_pipeline)  │                              │
│              │                              │                              │
│              └──────────────┬───────────────┘                              │
│                             │                                              │
│         ┌───────────────────┼───────────────────┐                          │
│         │                   │                   │                          │
│         ▼                   ▼                   ▼                          │
│  ┌─────────────┐    ┌──────────────┐   ┌──────────────┐                  │
│  │ ROI         │    │ ROI          │   │ ROI Damage   │                  │
│  │ Detector    │    │ Enhancer     │   │ Detector     │                  │
│  │ (YOLO)      │    │ (Task-based) │   │ (Heuristic)  │                  │
│  └─────────────┘    └──────────────┘   └──────────────┘                  │
│                                                                             │
│                             │                                              │
│                             ▼                                              │
│              ┌──────────────────────────────┐                              │
│              │   OUTPUT STORAGE             │                              │
│              │   - Wagon number crops       │                              │
│              │   - Damage crops (annotated) │                              │
│              │   - Metadata JSON            │                              │
│              └──────────────┬───────────────┘                              │
│                             │                                              │
│                             ▼                                              │
│              ┌──────────────────────────────┐                              │
│              │   FRONTEND DISPLAY           │                              │
│              │   - Wagon numbers list       │                              │
│              │   - Damage detections        │                              │
│              │   - Historical records       │                              │
│              └──────────────────────────────┘                              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Frame Processing Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│ INPUT: Video Frame (1920x1080, BGR)                            │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
        ┌────────────────────────────────────┐
        │ OPTIONAL: Global Enhancement       │
        │ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
        │ IF enabled:                        │
        │   • Bilateral filter (d=5)         │
        │   • CLAHE (clip_limit=1.0)         │
        │   • Slight sharpen                 │
        │ ELSE:                              │
        │   • Skip (raw frame)               │
        └────────────┬───────────────────────┘
                     │
                     ▼
        ┌────────────────────────────────────┐
        │ STAGE 1: YOLOv8 Detection          │
        │ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
        │ Detect:                            │
        │   • wagon_number (confidence > 0.4)│
        │   • window (confidence > 0.4)      │
        │   • door (confidence > 0.4)        │
        │                                    │
        │ Output: List of ROI detections     │
        └────────────┬───────────────────────┘
                     │
                     ▼
          ┌──────────┴──────────┐
          │                     │
          ▼                     ▼
┌─────────────────────┐  ┌─────────────────────┐
│ ROI Type:           │  │ ROI Type:           │
│ wagon_number        │  │ window / door       │
└──────────┬──────────┘  └──────────┬──────────┘
           │                        │
           ▼                        ▼
┌─────────────────────┐  ┌─────────────────────┐
│ AGGRESSIVE          │  │ MILD                │
│ ENHANCEMENT         │  │ ENHANCEMENT         │
│ ━━━━━━━━━━━━━━━━   │  │ ━━━━━━━━━━━━━━━━   │
│ 1. Denoise          │  │ 1. Bilateral filter │
│ 2. CLAHE (3.0)      │  │ 2. CLAHE (1.5)      │
│ 3. Sharpen          │  │ 3. Slight sharpen   │
│ 4. Adaptive thresh  │  │                     │
│ 5. Morphology       │  │                     │
└──────────┬──────────┘  └──────────┬──────────┘
           │                        │
           ▼                        ▼
┌─────────────────────┐  ┌─────────────────────┐
│ OCR PROCESSING      │  │ DAMAGE DETECTION    │
│ ━━━━━━━━━━━━━━━━   │  │ ━━━━━━━━━━━━━━━━   │
│ EasyOCR:            │  │ Heuristics:         │
│ • Read text         │  │ • Crack detection   │
│ • Extract wagon #   │  │ • Glass damage      │
│ • Confidence score  │  │ • Deformation       │
│                     │  │                     │
│ Output:             │  │ Output:             │
│ {                   │  │ {                   │
│   text: "ABC123"    │  │   has_damage: True  │
│   conf: 0.92        │  │   type: "crack"     │
│ }                   │  │   conf: 0.87        │
│                     │  │ }                   │
└──────────┬──────────┘  └──────────┬──────────┘
           │                        │
           └────────┬───────────────┘
                    │
                    ▼
         ┌──────────────────────┐
         │ RESULT AGGREGATION   │
         │ ━━━━━━━━━━━━━━━━━   │
         │ Combine:             │
         │ • All wagon numbers  │
         │ • All damage detects │
         │ • Frame metadata     │
         └──────────┬───────────┘
                    │
                    ▼
         ┌──────────────────────┐
         │ SAVE OUTPUTS         │
         │ ━━━━━━━━━━━━━━━━━   │
         │ 1. Crop wagon #      │
         │ 2. Crop damage       │
         │ 3. Annotate damage   │
         │ 4. Save metadata     │
         └──────────┬───────────┘
                    │
                    ▼
         ┌──────────────────────┐
         │ OUTPUT STRUCTURE     │
         │ ━━━━━━━━━━━━━━━━━   │
         │ records/             │
         │ └─ inspection_ID/    │
         │    ├─ wagon_numbers/ │
         │    ├─ damage/        │
         │    └─ metadata.json  │
         └──────────────────────┘
```

---

## Module Interaction Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│                   ROI INSPECTION PIPELINE                        │
│                 (roi_inspection_pipeline.py)                     │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ process_frame(frame)                                   │    │
│  │ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━    │    │
│  │                                                         │    │
│  │  1. Call: roi_detector.detect_rois(frame)              │    │
│  │            │                                            │    │
│  │            └──────────────────┐                         │    │
│  │                               │                         │    │
│  │            ┌──────────────────▼──────────────┐          │    │
│  │            │ ROI DETECTOR                    │          │    │
│  │            │ (roi_detector.py)               │          │    │
│  │            │ ━━━━━━━━━━━━━━━━━━━━━━━━━━━   │          │    │
│  │            │ • Load YOLO model               │          │    │
│  │            │ • Run inference                 │          │    │
│  │            │ • Filter by confidence          │          │    │
│  │            │ • Crop ROIs                     │          │    │
│  │            │                                 │          │    │
│  │            │ Return: List[Detection]         │          │    │
│  │            └──────────────────┬──────────────┘          │    │
│  │                               │                         │    │
│  │  2. For each detection:       │                         │    │
│  │                               │                         │    │
│  │     Call: roi_enhancer.enhance_roi(crop, class)        │    │
│  │            │                                            │    │
│  │            └──────────────────┐                         │    │
│  │                               │                         │    │
│  │            ┌──────────────────▼──────────────┐          │    │
│  │            │ ROI ENHANCER                    │          │    │
│  │            │ (roi_enhancer.py)               │          │    │
│  │            │ ━━━━━━━━━━━━━━━━━━━━━━━━━━━   │          │    │
│  │            │ IF class == 'wagon_number':     │          │    │
│  │            │   • enhance_for_ocr()           │          │    │
│  │            │ ELIF class in ['window','door']:│          │    │
│  │            │   • enhance_for_damage()        │          │    │
│  │            │                                 │          │    │
│  │            │ Return: Enhanced crop           │          │    │
│  │            └──────────────────┬──────────────┘          │    │
│  │                               │                         │    │
│  │  3a. If wagon_number:         │                         │    │
│  │                               │                         │    │
│  │     Call: ocr_reader.readtext(enhanced_crop)           │    │
│  │            │                                            │    │
│  │            └──────────────────┐                         │    │
│  │                               │                         │    │
│  │            ┌──────────────────▼──────────────┐          │    │
│  │            │ EASYOCR                         │          │    │
│  │            │ (external library)              │          │    │
│  │            │ ━━━━━━━━━━━━━━━━━━━━━━━━━━━   │          │    │
│  │            │ • Detect text regions           │          │    │
│  │            │ • Recognize characters          │          │    │
│  │            │ • Return text + confidence      │          │    │
│  │            └──────────────────┬──────────────┘          │    │
│  │                               │                         │    │
│  │  3b. If window/door:          │                         │    │
│  │                               │                         │    │
│  │     Call: damage_detector.analyze_damage(crop, class)  │    │
│  │            │                                            │    │
│  │            └──────────────────┐                         │    │
│  │                               │                         │    │
│  │            ┌──────────────────▼──────────────┐          │    │
│  │            │ ROI DAMAGE DETECTOR             │          │    │
│  │            │ (roi_damage_detector.py)        │          │    │
│  │            │ ━━━━━━━━━━━━━━━━━━━━━━━━━━━   │          │    │
│  │            │ • _detect_cracks()              │          │    │
│  │            │ • _detect_glass_damage()        │          │    │
│  │            │ • _detect_deformation()         │          │    │
│  │            │ • Compute confidence            │          │    │
│  │            │                                 │          │    │
│  │            │ Return: Damage result           │          │    │
│  │            └─────────────────────────────────┘          │    │
│  │                                                         │    │
│  │  4. Aggregate all results and return                   │    │
│  │                                                         │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Data Flow Diagram

```
┌─────────────┐
│ Video Frame │
│ (BGR Image) │
└──────┬──────┘
       │
       ▼
┌──────────────────────────────────────┐
│ YOLO Detection Result:               │
│ [                                    │
│   {                                  │
│     class: "wagon_number",           │
│     bbox: [100, 200, 150, 50],       │
│     confidence: 0.92,                │
│     crop: np.ndarray(50x150x3)       │
│   },                                 │
│   {                                  │
│     class: "window",                 │
│     bbox: [300, 400, 200, 150],      │
│     confidence: 0.87,                │
│     crop: np.ndarray(150x200x3)      │
│   }                                  │
│ ]                                    │
└──────┬─────────────────────┬─────────┘
       │                     │
       │ wagon_number ROI    │ window ROI
       │                     │
       ▼                     ▼
┌──────────────┐      ┌──────────────┐
│ Enhanced     │      │ Enhanced     │
│ wagon_number │      │ window       │
│ (binarized)  │      │ (mild)       │
└──────┬───────┘      └──────┬───────┘
       │                     │
       ▼                     ▼
┌──────────────┐      ┌──────────────┐
│ OCR Result:  │      │ Damage       │
│ {            │      │ Result:      │
│   text:      │      │ {            │
│   "ABC123",  │      │   has_damage:│
│   conf: 0.92 │      │   True,      │
│ }            │      │   type:      │
└──────┬───────┘      │   "crack",   │
       │              │   conf: 0.87 │
       │              │ }            │
       │              └──────┬───────┘
       │                     │
       └──────────┬──────────┘
                  │
                  ▼
       ┌────────────────────┐
       │ Aggregated Results │
       │ {                  │
       │   wagon_numbers: [ │
       │     {              │
       │       text:        │
       │       "ABC123",    │
       │       conf: 0.92   │
       │     }              │
       │   ],               │
       │   damage: [        │
       │     {              │
       │       type:        │
       │       "crack",     │
       │       conf: 0.87,  │
       │       class:       │
       │       "window"     │
       │     }              │
       │   ]                │
       │ }                  │
       └────────┬───────────┘
                │
                ▼
       ┌────────────────────┐
       │ Save to Disk:      │
       │                    │
       │ records/           │
       │ └─ inspection_ID/  │
       │    ├─ wagon_numbers│
       │    │  └─ ABC123.jpg│
       │    ├─ damage/      │
       │    │  └─ crack.jpg │
       │    └─ metadata.json│
       └────────────────────┘
```

---

## Enhancement Strategy Decision Tree

```
                           ROI Detected
                                │
                ┌───────────────┴───────────────┐
                │                               │
         class == "wagon_number"         class in ["window", "door"]
                │                               │
                ▼                               ▼
        ┌───────────────┐              ┌────────────────┐
        │  AGGRESSIVE   │              │     MILD       │
        │  ENHANCEMENT  │              │  ENHANCEMENT   │
        └───────┬───────┘              └────────┬───────┘
                │                               │
                ▼                               ▼
    ┌───────────────────────┐      ┌───────────────────────┐
    │ 1. Bilateral denoise  │      │ 1. Bilateral filter   │
    │ 2. CLAHE (clip=3.0)   │      │ 2. CLAHE (clip=1.5)   │
    │ 3. Sharpen (strong)   │      │ 3. Sharpen (slight)   │
    │ 4. Adaptive threshold │      │                       │
    │ 5. Morphology close   │      │                       │
    └───────────┬───────────┘      └───────────┬───────────┘
                │                               │
                ▼                               ▼
         ┌──────────┐                   ┌──────────────┐
         │   OCR    │                   │    DAMAGE    │
         │          │                   │  DETECTION   │
         └──────────┘                   └──────────────┘
```

---

## Damage Detection Logic

```
        Enhanced Window/Door ROI
                 │
     ┌───────────┴───────────┐
     │                       │
     ▼                       ▼
┌─────────────┐     ┌─────────────────┐
│ Convert to  │     │ Convert to      │
│ Grayscale   │     │ Grayscale       │
└──────┬──────┘     └────────┬────────┘
       │                     │
       ▼                     ▼
┌─────────────┐     ┌─────────────────┐
│ CRACK       │     │ GLASS DAMAGE    │
│ DETECTION   │     │ DETECTION       │
│ ━━━━━━━━━   │     │ ━━━━━━━━━━━━   │
│             │     │                 │
│ 1. Canny    │     │ 1. Laplacian    │
│    edges    │     │    variance     │
│ 2. Find     │     │ 2. Threshold    │
│    contours │     │    (blur check) │
│ 3. Filter   │     │ 3. Bright spot  │
│    elongated│     │    detection    │
│ 4. Variance │     │ 4. Score        │
│    score    │     │    combination  │
│             │     │                 │
│ Score:      │     │ Score:          │
│ crack_var   │     │ glass_score     │
└──────┬──────┘     └────────┬────────┘
       │                     │
       │                     │
       ▼                     ▼
┌──────────────────────────────────┐
│ DEFORMATION DETECTION            │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│                                  │
│ 1. Find contours                 │
│ 2. Measure circularity           │
│ 3. Compute irregularity          │
│ 4. Aspect ratio analysis         │
│                                  │
│ Score: deform_score              │
└────────────┬─────────────────────┘
             │
             ▼
┌────────────────────────────────┐
│ COMPARE SCORES                 │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│                                │
│ max_score = max(               │
│     crack_var,                 │
│     glass_score,               │
│     deform_score               │
│ )                              │
│                                │
│ IF max_score > threshold:      │
│     has_damage = True          │
│     type = score_with_max      │
│ ELSE:                          │
│     has_damage = False         │
└────────────┬───────────────────┘
             │
             ▼
┌────────────────────────────────┐
│ RETURN RESULT                  │
│ {                              │
│   has_damage: True/False,      │
│   damage_type: "crack" etc,    │
│   confidence: 0.0-1.0,         │
│   damage_score: {...},         │
│   details: {...}               │
│ }                              │
└────────────────────────────────┘
```

---

## File Organization

```
railway_dashboard/backend/
│
├─ ROI PIPELINE MODULES (NEW):
│  ├─ roi_detector.py              ← YOLO wrapper
│  ├─ roi_enhancer.py              ← Enhancement strategies
│  ├─ roi_damage_detector.py       ← Damage heuristics
│  └─ roi_inspection_pipeline.py   ← Main orchestrator
│
├─ ROI DOCUMENTATION (NEW):
│  ├─ ROI_PIPELINE_ARCHITECTURE.md ← Full architecture
│  ├─ ROI_PIPELINE_INTEGRATION.md  ← Integration guide
│  ├─ ROI_COMPLETE_SUMMARY.md      ← Complete summary
│  ├─ ROI_QUICK_REFERENCE.md       ← Quick reference
│  └─ ROI_VISUAL_DIAGRAMS.md       ← This file
│
├─ EXISTING BACKEND:
│  ├─ app.py                       ← Flask API
│  ├─ inspection_processor.py      ← Legacy processor
│  ├─ damage_detector.py           ← Legacy damage detection
│  └─ ...
│
└─ MODELS (TO BE ADDED):
   └─ wagon_detector.pt            ← Trained YOLO model
```

---

## Deployment Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                        PRODUCTION DEPLOYMENT                 │
└──────────────────────────────────────────────────────────────┘

    ┌─────────────┐
    │   CLIENT    │
    │  (Browser)  │
    └──────┬──────┘
           │ HTTP
           ▼
    ┌─────────────┐
    │   NGINX     │ (Reverse Proxy)
    │   (Port 80) │
    └──────┬──────┘
           │
           ▼
    ┌─────────────────┐
    │   FLASK APP     │ (Gunicorn)
    │   (Port 5000)   │
    │                 │
    │ ┌─────────────┐ │
    │ │ ROI Pipeline│ │
    │ │ ┌─────────┐ │ │
    │ │ │ YOLO    │ │ │ (GPU)
    │ │ └─────────┘ │ │
    │ │ ┌─────────┐ │ │
    │ │ │ EasyOCR │ │ │ (GPU)
    │ │ └─────────┘ │ │
    │ └─────────────┘ │
    └────────┬────────┘
             │
             ▼
    ┌─────────────────┐
    │  FILE STORAGE   │
    │  (records/)     │
    │                 │
    │  ├─ wagon_nums  │
    │  ├─ damage      │
    │  └─ metadata    │
    └─────────────────┘
```

---

**Author**: Railway Wagon Inspection System  
**Date**: January 4, 2026  
**Purpose**: Visual documentation for ROI-based inspection pipeline  
