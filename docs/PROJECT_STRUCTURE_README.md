# RAILwagon Inspection System - Project Structure

## Project Overview

A comprehensive railway wagon inspection system that performs real-time and recorded video analysis, deblurring, OCR for wagon number detection, and damage detection using AI/ML models.

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    USER INTERFACE (Web Browser)              │
│              Railway Dashboard (HTML/CSS/JavaScript)         │
└─────────────────┬───────────────────────────────────────────┘
                  │ HTTP/WebSocket
                  ▼
┌─────────────────────────────────────────────────────────────┐
│              BACKEND API SERVER (Flask - Python)             │
│                    Port: 5000                                 │
├─────────────────────────────────────────────────────────────┤
│  • REST API Endpoints                                        │
│  • Session Management                                        │
│  • File Upload/Download                                      │
│  • Real-time Event Streaming (SSE)                          │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│           INSPECTION PROCESSOR (Core Engine)                 │
├─────────────────────────────────────────────────────────────┤
│  1. Video Frame Extraction                                   │
│  2. Motion Detection (Auto Mode)                            │
│  3. Deblurring Pipeline                                      │
│  4. OCR Processing (Tesseract)                              │
│  5. Damage Detection (YOLOv8)                               │
│  6. ROI (Region of Interest) Processing                     │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│                   AI/ML MODELS & LIBRARIES                    │
├─────────────────────────────────────────────────────────────┤
│  • PyTorch (Deep Learning Framework)                         │
│  • NAFNet (Deblurring Model)                                │
│  • YOLOv8 (Damage Detection)                                │
│  • Tesseract OCR (Text Recognition)                         │
│  • OpenCV (Computer Vision)                                  │
│  • EasyOCR (Alternative OCR)                                │
└─────────────────────────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│                   DATA STORAGE                               │
├─────────────────────────────────────────────────────────────┤
│  • sessions/          - Active inspection sessions           │
│  • sessions_deleted/  - Recently deleted (7-day retention)  │
│  • uploads/          - Uploaded video files                  │
│  • models/           - Pretrained AI models                  │
└─────────────────────────────────────────────────────────────┘
```

---

## Directory Structure

```
blur/
│
├── railway_dashboard/              # Main Dashboard Application
│   ├── index.html                  # Main UI (Login, Dashboard, Pages)
│   ├── script.js                   # Frontend Logic (3000+ lines)
│   ├── style.css                   # Cyberpunk Theme Styling
│   │
│   └── backend/                    # Flask Backend Server
│       ├── app.py                  # Main API Server (1200+ lines)
│       ├── inspection_processor.py # Core Processing Engine
│       ├── roi_inspection_pipeline.py  # ROI-based processing
│       ├── roi_detector.py         # ROI detection
│       ├── roi_enhancer.py         # Image enhancement
│       ├── roi_damage_detector.py  # Damage detection in ROI
│       ├── damage_detector.py      # General damage detection
│       ├── sessions/               # Active session data
│       ├── sessions_deleted/       # Recently deleted sessions
│       └── uploads/                # Uploaded videos/images
│
├── models/                         # AI/ML Model Files
│   ├── NAFNet-GoPro-width64.pth   # Deblurring model
│   └── best.pt                     # YOLOv8 damage detection
│
├── temporal_fusion_wagon.py        # Temporal fusion for wagon tracking
├── ocr_pipeline.py                 # OCR processing pipeline
├── process_railway_video.py        # Video processing scripts
├── motion_gate_droidcam.py        # Motion detection
└── droidcam_config.py             # Camera configuration
```

---

## Component Breakdown

### 1. Frontend (Railway Dashboard)

**Files:** `index.html`, `script.js`, `style.css`

**Pages:**
- **Login Screen** - Operator authentication
- **Live Video Inspection** - Real-time camera feed processing
- **Recorded Video Inspection** - Upload and process video files
- **Image Inspection** - Single image analysis
- **Analysis** - Aggregated statistics and insights
- **Records** - Session history with Recently Deleted feature

**Key Features:**
- Motion Detection Auto Mode (with train simulation)
- Real-time frame display during inspection
- Deblurred frame previews
- Wagon number detection visualization
- Damage detection alerts
- Before/After comparison viewer
- Session management with soft delete (7-day retention)

---

### 2. Backend API Server

**File:** `railway_dashboard/backend/app.py`

**Core Responsibilities:**
- Handle HTTP requests from frontend
- Manage inspection sessions
- Process live video streams
- Handle file uploads
- Serve session data and images
- Real-time event streaming (SSE)

**Main API Endpoints:**

#### Live Video
```
POST   /api/live/start          - Start live video feed
POST   /api/live/stop           - Stop live video feed
GET    /api/stream              - Server-Sent Events stream
```

#### Inspection
```
POST   /api/inspection/start    - Start inspection (live/recorded)
POST   /api/inspection/stop     - Stop active inspection
GET    /api/inspection/status   - Get current inspection status
```

#### Image Processing
```
POST   /api/image/process       - Process single image
```

#### Sessions
```
GET    /api/sessions            - Get all active sessions
GET    /api/session/<id>        - Get specific session details
DELETE /api/session/<id>        - Soft delete session (move to deleted)
POST   /api/session/<id>/restore - Restore deleted session
DELETE /api/session/<id>/permanent-delete - Permanently delete
GET    /api/deleted-sessions    - Get recently deleted sessions
POST   /api/cleanup-old-deletions - Auto-cleanup sessions >7 days
```

#### Analytics
```
GET    /api/analytics           - Get aggregated statistics
```

#### Files
```
GET    /api/sessions/<path>     - Serve session files
GET    /api/session/<id>/image/<filename> - Get specific image
```

---

### 3. Inspection Processor (Core Engine)

**File:** `railway_dashboard/backend/inspection_processor.py`

**Processing Pipeline:**

```
Video Input
    ↓
Frame Extraction (30 FPS)
    ↓
Motion Detection (optional)
    ↓
Blur Quality Assessment
    ↓
[If Blurred] → Deblurring (NAFNet)
    ↓
OCR Processing (Tesseract)
    ↓
Wagon Number Detection
    ↓
Damage Detection (YOLOv8)
    ↓
Results Storage & Visualization
```

**Key Methods:**
- `start_live_inspection()` - Live camera feed processing
- `process_recorded_video()` - Batch video processing
- `process_single_image()` - Single image analysis
- `deblur_frame()` - Apply NAFNet deblurring
- `detect_wagon_number()` - OCR for wagon identification
- `detect_damage()` - YOLO-based damage detection
- `save_session_results()` - Persist inspection data

---

### 4. ROI Processing Pipeline

**Files:** 
- `roi_inspection_pipeline.py` - Main ROI workflow
- `roi_detector.py` - Detect regions of interest
- `roi_enhancer.py` - Enhance ROI quality
- `roi_damage_detector.py` - Damage detection in ROI

**Purpose:** Focus processing on specific regions (wagon numbers, damage areas) for improved accuracy and performance.

---

### 5. Motion Detection System

**File:** `motion_gate_droidcam.py`

**Auto Mode States:**
```
IDLE
  ↓ (Motion Detected)
MOTION_DETECTED
  ↓ (10 consecutive motion frames)
TRAIN_CONFIRMED
  ↓ (Auto-start inspection)
INSPECTION_RUNNING
  ↓ (60 frames no motion)
AUTO_STOP → IDLE
```

**Parameters:**
- Motion Threshold: 15%
- Confirmation Frames: 10
- No-Motion Stop Frames: 60
- Background Subtraction: MOG2

---

### 6. OCR Pipeline

**Files:** `ocr_pipeline.py`, `text_enhancement.py`

**OCR Workflow:**
```
Input Image
    ↓
Preprocessing (Grayscale, Denoise)
    ↓
Text Enhancement (CLAHE, Thresholding)
    ↓
OCR Engine (Tesseract/EasyOCR)
    ↓
Post-processing (Filtering, Validation)
    ↓
Wagon Number Extraction
```

**Supported Formats:**
- NR-XXXXX (Indian Railways)
- XXXXX (Numeric only)
- Pattern validation and confidence scoring

---

### 7. Damage Detection

**Files:** `damage_detector.py`, `roi_damage_detector.py`

**Model:** YOLOv8 (trained on railway damage dataset)

**Detection Classes:**
- Cracks
- Dents
- Corrosion
- Missing parts
- Structural damage

**Output:**
- Bounding boxes
- Confidence scores
- Damage type labels
- Annotated images

---

### 8. Temporal Fusion

**File:** `temporal_fusion_wagon.py`

**Purpose:** Track wagon numbers across multiple frames to improve accuracy.

**Features:**
- Cross-frame number matching
- Confidence boosting
- False positive reduction
- Temporal consistency checks

---

## Data Flow

### Live Video Inspection Flow

```
1. User clicks "Start Live Video"
   ↓
2. Frontend → POST /api/live/start
   ↓
3. Backend opens camera feed (DroidCam/Webcam)
   ↓
4. User clicks "Start Inspection"
   ↓
5. Frontend → POST /api/inspection/start (type: live)
   ↓
6. Backend creates session ID
   ↓
7. Processing loop starts:
   - Extract frame
   - Check motion (if auto mode)
   - Assess blur
   - Deblur if needed
   - OCR processing
   - Damage detection
   - Save results
   ↓
8. Results streamed via SSE → Frontend updates UI
   ↓
9. User clicks "Stop Inspection"
   ↓
10. Backend saves session → sessions/<session_id>/
```

### Recorded Video Inspection Flow

```
1. User selects video file
   ↓
2. Frontend → POST /api/inspection/start (type: recorded, video_path)
   ↓
3. Backend processes video:
   - Frame-by-frame extraction
   - Deblurring pipeline
   - OCR on each frame
   - Damage detection
   - Progress updates via SSE
   ↓
4. Final results saved to session
   ↓
5. Frontend displays results in tabs
```

### Session Management Flow

```
Active Session Creation
   ↓
Saved to: sessions/<session_id>/
   - metadata.json
   - wagon_detections/
   - deblurred/
   - frames/
   - damage/
   ↓
User deletes session
   ↓
Moved to: sessions_deleted/<session_id>/
   - metadata.json updated with deleted_at
   - 7-day retention timer starts
   ↓
User can restore (within 7 days)
   ↓
Moved back to: sessions/<session_id>/
   ↓
OR
   ↓
Auto-cleanup after 7 days (permanent delete)
```

---

## Key Technologies

### Backend
- **Flask** - Web framework
- **PyTorch** - Deep learning
- **OpenCV** - Computer vision
- **NumPy** - Numerical computing
- **Pillow** - Image processing
- **Tesseract OCR** - Text recognition
- **Ultralytics (YOLOv8)** - Object detection

### Frontend
- **HTML5** - Structure
- **CSS3** - Cyberpunk styling
- **Vanilla JavaScript** - Logic (no frameworks)
- **Server-Sent Events (SSE)** - Real-time updates
- **Fetch API** - HTTP requests

### AI Models
- **NAFNet** - Image deblurring (GoPro trained)
- **YOLOv8** - Damage detection
- **Tesseract** - OCR engine

---

## Session Data Structure

### Active Session Directory
```
sessions/<session_id>/
├── metadata.json              # Session info
├── wagon_detections/         # Detected wagon images
│   ├── wagon_NR-12345_001.jpg
│   ├── wagon_NR-12346_025.jpg
│   └── damage_001.jpg
├── deblurred/               # Deblurred frames
│   ├── deblurred_000001.jpg
│   └── deblurred_000005.jpg
└── frames/                  # Original frames
    ├── frame_000001.jpg
    └── frame_000005.jpg
```

### Metadata JSON Structure
```json
{
  "session_id": "1704678912345",
  "type": "live",
  "operator": "John Doe",
  "start_time": "2026-01-07T10:30:00",
  "end_time": "2026-01-07T10:35:00",
  "results": {
    "wagons_detected": 15,
    "readable": 13,
    "unreadable": 2,
    "duration": 300,
    "avg_confidence": 0.87
  },
  "wagon_numbers": [
    {
      "number": "NR-12345",
      "frame": 10,
      "confidence": 0.92,
      "wagon_base64": "data:image/jpeg;base64,..."
    }
  ],
  "damage_detections": [
    {
      "frame": 15,
      "type": "crack",
      "confidence": 0.88,
      "bbox": [100, 200, 300, 400]
    }
  ]
}
```

---

## UI State Management

### AppState Object (JavaScript)
```javascript
AppState = {
    currentUser: { name, email },
    currentPage: "liveVideo|recordedVideo|...",
    currentSessionId: "timestamp_id",
    inspectionSessions: [...],
    deletedSessions: [...],
    currentRecordsTab: "active|deleted",
    analysisEnabled: true/false,
    liveVideoActive: true/false,
    liveInspectionActive: true/false,
    recordedInspectionActive: true/false,
    motionDetection: {
        autoMode: true/false,
        currentState: "IDLE|MOTION_DETECTED|...",
        motionFrameCount: 0,
        currentMotionLevel: 0
    }
}
```

---

## Features Summary

### Core Features
✅ Live video inspection from camera
✅ Recorded video batch processing
✅ Single image analysis
✅ Real-time deblurring (NAFNet)
✅ OCR wagon number detection
✅ AI damage detection (YOLOv8)
✅ Motion detection auto mode
✅ Session management
✅ Analytics dashboard
✅ Before/After comparison viewer

### Advanced Features
✅ Recently Deleted (7-day soft delete)
✅ Restore deleted sessions
✅ Custom confirmation modals (themed)
✅ Sticky sidebar and system panel
✅ Tabbed record detail view
✅ Side-by-side comparison modal
✅ Real-time progress updates (SSE)
✅ Train simulation for testing
✅ ROI-based processing
✅ Temporal fusion

---

## Configuration Files

### Key Config Files
- `droidcam_config.py` - Camera settings
- `motion_gate_config.py` - Motion detection params
- `requirements.txt` - Python dependencies
- `models/` - Pretrained model weights

---

## Performance Optimization

### Techniques Used
1. **Frame Skipping** - Process every Nth frame
2. **ROI Processing** - Focus on specific regions
3. **GPU Acceleration** - CUDA for PyTorch models
4. **Lazy Loading** - Load images on demand
5. **Thumbnail Generation** - Reduce data transfer
6. **Caching** - Store processed results
7. **Background Processing** - Async video processing

---

## Error Handling

### Backend
- Try-catch blocks for all API endpoints
- Graceful model loading failures
- Session cleanup on errors
- Detailed logging

### Frontend
- Custom error modals
- Validation before API calls
- Fallback UI states
- User-friendly error messages

---

## Future Enhancements (Planned)

1. **Database Integration** - PostgreSQL for sessions
2. **User Authentication** - JWT tokens
3. **Multi-camera Support** - Process multiple feeds
4. **Export Reports** - PDF/Excel generation
5. **Email Notifications** - Alert on damage detection
6. **Batch Operations** - Process multiple videos
7. **Cloud Storage** - AWS S3 integration
8. **Mobile App** - React Native companion
9. **Real-time Collaboration** - Multiple operators
10. **API Rate Limiting** - Prevent abuse

---

## Deployment Notes

### Development
```bash
cd railway_dashboard/backend
python app.py
# Server starts on http://localhost:5000
```

### Production Considerations
- Use Gunicorn/uWSGI for WSGI server
- Nginx reverse proxy
- SSL/TLS certificates
- Environment variables for secrets
- Docker containerization
- Load balancing for scale

---

## System Requirements

### Hardware
- CPU: 4+ cores recommended
- RAM: 8GB minimum, 16GB recommended
- GPU: NVIDIA CUDA-compatible (optional, for speed)
- Storage: 50GB+ for models and sessions

### Software
- Python 3.8+
- CUDA 11.0+ (if using GPU)
- Tesseract OCR 4.0+
- Modern web browser (Chrome/Firefox/Edge)

---

## Diagram Suggestions

### For Creating Structural Diagram

1. **System Architecture Diagram**
   - Show: Browser → Flask API → Processor → Models → Storage
   - Include: Data flow arrows, component boundaries

2. **Component Interaction Diagram**
   - Show: How frontend pages interact with backend endpoints
   - Include: Request/response cycle

3. **Data Flow Diagram**
   - Show: Live inspection flow step-by-step
   - Include: Decision points (motion detection, blur check)

4. **Session Lifecycle Diagram**
   - Show: Create → Active → Deleted → Restored/Permanent Delete
   - Include: Time-based transitions

5. **Processing Pipeline Diagram**
   - Show: Frame → Deblur → OCR → Damage → Results
   - Include: Parallel processing paths

6. **UI Navigation Flow**
   - Show: Login → Dashboard → Pages → Modals
   - Include: User actions and state changes

---

This README provides comprehensive structural information for creating detailed diagrams of the RAILwagon Inspection System.
