# Analysis Feature - Top 10 Frames Implementation

## Overview

Implemented a new analysis feature that allows users to:
1. View all recorded inspection sessions
2. Select a specific session
3. View the top 10 frames from that session, ranked by deblur quality

## Features Implemented

### 1. Session List View
- Displays all recorded inspections in a grid layout
- Shows key metrics for each session:
  - Session ID
  - Inspection type (Live/Recorded)
  - Wagons detected
  - Readable/Unreadable counts
  - Duration
  - Timestamp
- Click any session card to view its top 10 frames

### 2. Top 10 Frames View
- Automatically calculates frame quality using:
  - **Laplacian variance** (sharpness metric)
  - **Edge density** (detail preservation)
  - Combined quality score (0-100)
- Compares original vs deblurred quality
- Shows improvement percentage
- Displays wagon numbers (if detected)
- Includes frame previews
- Shows top 10 frames sorted by quality (highest first)

### 3. Quality Metrics

**Quality Score Calculation:**
```python
# Sharpness (Laplacian variance)
laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()

# Edge density
edges = cv2.Canny(gray, 100, 200)
edge_density = np.sum(edges > 0) / edges.size

# Combined quality (0-100)
quality_score = min(100, (laplacian_var / 10) + (edge_density * 200))
```

**Improvement Calculation:**
```python
improvement = deblurred_quality - original_quality
improvement_pct = (improvement / (original_quality + 1)) * 100
```

## Files Modified

### Backend (app.py)
1. **New Endpoint: `/api/sessions/list`**
   - Returns all recorded inspection sessions
   - Sorted by timestamp (newest first)
   - Includes session metadata and statistics

2. **New Endpoint: `/api/session/<session_id>/top-frames`**
   - Analyzes all deblurred frames from a session
   - Calculates quality scores for each frame
   - Compares with original frames
   - Returns top 10 frames sorted by quality
   - Includes wagon numbers if available

### Frontend (index.html)
- Updated analysis page structure
- Added session selection section
- Added top 10 frames table with new columns:
  - Rank
  - Frame ID
  - Original Quality
  - Deblurred Quality
  - Improvement %
  - Wagon Number
  - Preview Image
- Added back button to return to session selection

### Frontend (style.css)
- Added `.session-selection-grid` - Grid layout for session cards
- Added `.session-card` - Individual session card styling
- Added `.session-info-row` - Session metadata rows
- Added `.btn-back` - Back button styling
- Added `.session-info-bar` - Selected session info display

### Frontend (script.js)
1. **`loadAnalysisSessions()`** - Fetches and displays all sessions
2. **`displaySessionSelection(sessions)`** - Renders session grid
3. **`loadSessionTopFrames(sessionId)`** - Loads top 10 frames for selected session
4. **`displayTopFrames(data)`** - Renders top frames table
5. **`backToSessionSelection()`** - Returns to session list
6. **`viewFrameDetail()`** - View individual frame (placeholder for future enhancement)

## User Flow

```
1. User clicks "ANALYSIS" in navigation
   ↓
2. System displays all recorded inspections in grid
   ↓
3. User selects a specific inspection session
   ↓
4. System analyzes all frames and calculates quality scores
   ↓
5. System displays top 10 frames ranked by quality
   ↓
6. User can click "BACK TO SESSIONS" to select another session
```

## API Endpoints

### GET `/api/sessions/list`
**Response:**
```json
{
  "status": "success",
  "sessions": [
    {
      "id": "session_20260105_143022",
      "timestamp": "2026-01-05T14:30:22",
      "type": "live_video",
      "wagons_detected": 5,
      "readable": 4,
      "unreadable": 1,
      "duration": 45,
      "status": "completed"
    }
  ],
  "count": 10
}
```

### GET `/api/session/<session_id>/top-frames`
**Response:**
```json
{
  "status": "success",
  "session_id": "session_20260105_143022",
  "session_info": {
    "timestamp": "2026-01-05T14:30:22",
    "type": "live_video",
    "wagons_detected": 5
  },
  "top_frames": [
    {
      "frame_number": 142,
      "frame_id": "frame_000142",
      "quality_score": 87.52,
      "original_quality": 45.23,
      "improvement": 42.29,
      "improvement_pct": 93.5,
      "wagon_number": "NR-12345-6",
      "deblurred_path": "deblurred/deblurred_000142.jpg",
      "original_path": "frames/frame_000142.jpg"
    }
  ],
  "total_frames": 450
}
```

## Quality Score Interpretation

| Score Range | Quality | Description |
|-------------|---------|-------------|
| 90-100 | Excellent | Very sharp, high detail |
| 75-89 | Good | Clear and readable |
| 60-74 | Fair | Acceptable quality |
| 40-59 | Poor | Low sharpness |
| 0-39 | Very Poor | Blurry, low detail |

## Example Output

**Session Card:**
```
┌─────────────────────────────────┐
│ session_20260105_143022    LIVE │
├─────────────────────────────────┤
│ Wagons Detected:              5 │
│ Readable:                     4 │
│ Unreadable:                   1 │
│ Duration:                   45s │
│                                 │
│        Jan 5, 2026 02:30 PM     │
└─────────────────────────────────┘
```

**Top Frames Table:**
```
┌──────┬──────────────┬─────────┬──────────┬────────────┬──────────────┬─────────┐
│ RANK │ FRAME ID     │ ORIG    │ DEBLUR   │ IMPROVE    │ WAGON NUMBER │ PREVIEW │
├──────┼──────────────┼─────────┼──────────┼────────────┼──────────────┼─────────┤
│  1   │ frame_000142 │ 45.23   │ 87.52    │ +93.5%     │ NR-12345-6   │ [img]   │
│  2   │ frame_000205 │ 52.10   │ 85.30    │ +63.7%     │ NR-12345-7   │ [img]   │
│  3   │ frame_000089 │ 48.90   │ 84.12    │ +72.0%     │ N/A          │ [img]   │
└──────┴──────────────┴─────────┴──────────┴────────────┴──────────────┴─────────┘
```

## Performance Considerations

- Frame analysis is performed on-demand when session is selected
- Caches quality scores during analysis
- Processes only top 10 frames (sorted by score)
- Image previews load lazily
- Total frames count shown for reference

## Future Enhancements

1. **Frame Detail Modal** - Click frame to view full-size comparison
2. **Export Top Frames** - Download top frames as ZIP
3. **Quality Filters** - Filter by minimum quality threshold
4. **Comparison View** - Side-by-side before/after comparison
5. **Chart Visualization** - Quality distribution chart
6. **Session Comparison** - Compare top frames across multiple sessions

## Testing

To test the feature:

1. **Complete an inspection** (live or recorded)
2. **Navigate to Analysis page**
3. **Click on a session card**
4. **View top 10 frames** ranked by quality
5. **Click "BACK TO SESSIONS"** to select another session

The system will automatically calculate quality scores and show the highest-quality deblurred frames from each session!
