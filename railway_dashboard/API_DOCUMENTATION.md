# API Documentation - rAIlwagon System

## Base URL
```
http://localhost:5000/api
```

## Authentication
Currently no authentication required (can be added for production).

---

## Incident Management Endpoints

### 1. Get All Incidents
**Endpoint**: `GET /api/incidents`

**Description**: Retrieve all incidents with optional filtering

**Query Parameters**:
- `severity` (optional): Filter by severity (critical, high, medium, low)
- `status` (optional): Filter by status (detected, acknowledged, in_progress, resolved, escalated)
- `type` (optional): Filter by type (wagon_damage, ocr_failure, system_error, quality_issue)

**Response**:
```json
{
  "success": true,
  "incidents": [
    {
      "id": "INC-20260107120000",
      "type": "wagon_damage",
      "severity": "critical",
      "status": "resolved",
      "title": "Severe structural damage on wagon NR-12345",
      "description": "Cracked support beam detected...",
      "detected_at": "2026-01-07T12:00:00",
      "resolved_at": "2026-01-07T14:30:00",
      "wagon_number": "NR-12345",
      "confidence": 0.92,
      "response_time_minutes": 150.0,
      "recommended_actions": [
        "Immediately isolate affected wagon",
        "Dispatch maintenance team"
      ]
    }
  ],
  "total": 1
}
```

---

### 2. Get Incident by ID
**Endpoint**: `GET /api/incident/<incident_id>`

**Description**: Get detailed information about a specific incident

**Response**:
```json
{
  "success": true,
  "incident": {
    "id": "INC-20260107120000",
    "type": "wagon_damage",
    "severity": "critical",
    "status": "resolved",
    "title": "Severe structural damage on wagon NR-12345",
    "description": "Cracked support beam detected during routine inspection",
    "detected_at": "2026-01-07T12:00:00",
    "acknowledged_at": "2026-01-07T12:05:00",
    "resolved_at": "2026-01-07T14:30:00",
    "session_id": "1704628800000",
    "wagon_number": "NR-12345",
    "frame_number": 145,
    "damage_type": "structural",
    "confidence": 0.92,
    "root_cause": "Metal fatigue due to age",
    "resolution_steps": [
      "Wagon isolated from service",
      "Support beam replaced",
      "Full structural inspection completed",
      "Wagon certified for service"
    ],
    "assigned_to": "Maintenance Team A",
    "response_time_minutes": 150.0,
    "recommended_actions": [
      "Immediately isolate affected wagon from service",
      "Dispatch maintenance team for on-site inspection"
    ],
    "similar_incidents": [],
    "recommended_by_ai": true
  }
}
```

---

### 3. Find Similar Incidents
**Endpoint**: `GET /api/incident/<incident_id>/similar`

**Description**: Use AI to find similar past incidents based on semantic similarity

**Query Parameters**:
- `top_k` (optional): Number of similar incidents to return (default: 5)

**Response**:
```json
{
  "success": true,
  "incident_id": "INC-20260107120000",
  "similar_incidents": [
    {
      "incident": {
        "id": "INC-20251215093000",
        "type": "wagon_damage",
        "severity": "high",
        "title": "Support beam crack detected",
        "status": "resolved"
      },
      "similarity_score": 0.89,
      "rank": 1
    },
    {
      "incident": {
        "id": "INC-20251210141500",
        "type": "wagon_damage",
        "severity": "medium",
        "title": "Minor structural weakness identified",
        "status": "resolved"
      },
      "similarity_score": 0.76,
      "rank": 2
    }
  ]
}
```

**How It Works**:
1. Converts incident description to 384-dim embedding using Sentence-BERT
2. Searches FAISS vector index using L2 distance
3. Returns top-k most similar incidents with similarity scores
4. Similarity score: 1.0 = identical, 0.0 = completely different

---

### 4. Get AI Recommendations
**Endpoint**: `GET /api/incident/<incident_id>/recommendations`

**Description**: Get AI-powered action recommendations based on similar past incidents

**Response**:
```json
{
  "success": true,
  "incident_id": "INC-20260107120000",
  "recommended_actions": [
    "Immediately isolate affected wagon from service",
    "Dispatch maintenance team for on-site inspection",
    "Document damage with high-resolution photos",
    "Notify safety supervisor and operations manager",
    "Review maintenance logs for affected wagon"
  ],
  "based_on_similar_incidents": 5,
  "similar_incidents": [
    {
      "incident": { "id": "INC-20251215093000", "title": "..." },
      "similarity_score": 0.89,
      "rank": 1
    }
  ]
}
```

**Recommendation Logic**:
1. Finds top 5 similar resolved incidents
2. Extracts resolution steps from each
3. Ranks actions by frequency × similarity score
4. Returns top 5 most relevant recommendations

---

### 5. Create New Incident
**Endpoint**: `POST /api/incident`

**Description**: Create a new incident (manual or automated)

**Request Body**:
```json
{
  "type": "wagon_damage",
  "severity": "high",
  "title": "Broken window on wagon NR-45678",
  "description": "Shattered glass detected during inspection",
  "session_id": "1704628800000",
  "wagon_number": "NR-45678",
  "frame_number": 89,
  "damage_type": "broken_glass",
  "confidence": 0.87
}
```

**Response**:
```json
{
  "success": true,
  "incident_id": "INC-20260107150000",
  "recommended_actions": [
    "Schedule window replacement",
    "Clean surrounding area of glass shards",
    "Inspect adjacent windows for cracks"
  ]
}
```

---

### 6. Update Incident
**Endpoint**: `PUT /api/incident/<incident_id>`

**Description**: Update incident status, add notes, or mark as resolved

**Request Body**:
```json
{
  "status": "resolved",
  "root_cause": "Impact damage from debris",
  "resolution_steps": [
    "Window replaced with tempered glass",
    "Area inspected for additional damage",
    "Wagon cleared for service"
  ],
  "notes": "Completed by Team B on 2026-01-07"
}
```

**Response**:
```json
{
  "success": true,
  "incident_id": "INC-20260107150000"
}
```

**Auto-calculated Fields**:
- `acknowledged_at`: Set when status → acknowledged
- `resolved_at`: Set when status → resolved
- `response_time_minutes`: Auto-calculated from detection to resolution

---

### 7. Get Incident Statistics
**Endpoint**: `GET /api/incidents/stats`

**Description**: Get aggregated statistics and response time metrics

**Response**:
```json
{
  "success": true,
  "total_incidents": 23,
  "status_breakdown": {
    "detected": 3,
    "acknowledged": 5,
    "in_progress": 4,
    "resolved": 10,
    "escalated": 1
  },
  "severity_breakdown": {
    "critical": 2,
    "high": 7,
    "medium": 10,
    "low": 4
  },
  "response_time_stats": {
    "wagon_damage": {
      "avg_response_time": 45.3,
      "min_response_time": 12.5,
      "max_response_time": 180.0,
      "count": 15
    },
    "ocr_failure": {
      "avg_response_time": 8.7,
      "min_response_time": 3.2,
      "max_response_time": 25.0,
      "count": 8
    }
  },
  "recent_incidents": [
    { "id": "...", "title": "...", "severity": "..." }
  ]
}
```

---

## Inspection Endpoints

### 8. Start Live Video
**Endpoint**: `POST /api/live/start`

**Request Body**:
```json
{
  "video_source": 0
}
```

**Response**:
```json
{
  "status": "success",
  "message": "Live video started (Camera 0)",
  "video_source": "0"
}
```

---

### 9. Start Inspection
**Endpoint**: `POST /api/inspection/start`

**Request Body**:
```json
{
  "type": "live",
  "operator": "John Smith",
  "use_motion_detection": true
}
```

**Response**:
```json
{
  "status": "success",
  "session_id": "1704628800000",
  "message": "Inspection started"
}
```

---

### 10. Stop Inspection
**Endpoint**: `POST /api/inspection/stop`

**Request Body**:
```json
{
  "session_id": "1704628800000"
}
```

**Response**:
```json
{
  "status": "success",
  "message": "Inspection stopped",
  "results": {
    "frames_processed": 245,
    "wagons_detected": 12,
    "damage_incidents": 3,
    "ocr_success_rate": 0.95
  }
}
```

---

### 11. Get Inspection Status
**Endpoint**: `GET /api/inspection/status/<session_id>`

**Description**: Get real-time status of running inspection

**Response**:
```json
{
  "status": "success",
  "data": {
    "fps": 15,
    "latency": 67,
    "frames_processed": 145,
    "detections": 8,
    "motion_level": 23.5,
    "motion_state": "TRAIN_CONFIRMED",
    "train_confirmed": true,
    "wagon_numbers": [
      {
        "number": "NR-12345",
        "frame": 45,
        "wagon_base64": "data:image/jpeg;base64,..."
      }
    ],
    "damage_detections": [
      {
        "frame": 67,
        "damage_type": "structural",
        "confidence": 0.89,
        "damage_base64": "data:image/jpeg;base64,..."
      }
    ]
  }
}
```

---

### 12. Get All Sessions
**Endpoint**: `GET /api/sessions`

**Description**: Get all inspection sessions

**Response**:
```json
{
  "status": "success",
  "sessions": [
    {
      "id": "1704628800000",
      "type": "live",
      "operator": "John Smith",
      "start_time": "2026-01-07T10:00:00",
      "end_time": "2026-01-07T10:15:00",
      "status": "completed",
      "results": {
        "frames_processed": 245,
        "wagons_detected": 12,
        "damage_incidents": 3
      }
    }
  ]
}
```

---

### 13. Process Single Image
**Endpoint**: `POST /api/image/process`

**Request**: Multipart form data with image file

**Response**:
```json
{
  "status": "success",
  "data": {
    "original_path": "/uploads/image_1704628800_test.jpg",
    "deblurred_path": "/uploads/deblurred_1704628800_test.jpg",
    "wagon_number": "NR-12345",
    "damage_detected": true,
    "damage_type": "crack",
    "confidence": 0.87
  }
}
```

---

## Error Responses

All endpoints return errors in this format:

```json
{
  "success": false,
  "error": "Error message description"
}
```

**Common HTTP Status Codes**:
- `200 OK`: Request succeeded
- `400 Bad Request`: Invalid parameters
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error
- `503 Service Unavailable`: AI agent not available

---

## Rate Limits
Currently no rate limits (can be added for production).

---

## WebSocket Events (Future Enhancement)
Real-time updates via WebSocket for:
- Live inspection frame updates
- New incident notifications
- Status change events

---

## Example Usage (Python)

```python
import requests

BASE_URL = "http://localhost:5000/api"

# Get all critical incidents
response = requests.get(
    f"{BASE_URL}/incidents",
    params={"severity": "critical"}
)
incidents = response.json()["incidents"]

# Create new incident
new_incident = {
    "type": "wagon_damage",
    "severity": "high",
    "title": "Cracked wheel detected",
    "description": "Visual inspection revealed crack in wheel rim",
    "wagon_number": "NR-99999"
}
response = requests.post(f"{BASE_URL}/incident", json=new_incident)
incident_id = response.json()["incident_id"]

# Get AI recommendations
response = requests.get(f"{BASE_URL}/incident/{incident_id}/recommendations")
recommendations = response.json()["recommended_actions"]
print(f"AI Recommends: {recommendations}")
```

---

## Example Usage (JavaScript)

```javascript
// Get incident statistics
fetch('/api/incidents/stats')
  .then(res => res.json())
  .then(data => {
    console.log(`Total incidents: ${data.total_incidents}`);
    console.log(`Critical: ${data.severity_breakdown.critical}`);
  });

// Find similar incidents
fetch('/api/incident/INC-20260107120000/similar?top_k=3')
  .then(res => res.json())
  .then(data => {
    data.similar_incidents.forEach(item => {
      console.log(`Similar: ${item.incident.title} (${item.similarity_score})`);
    });
  });

// Update incident status
fetch('/api/incident/INC-20260107120000', {
  method: 'PUT',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ status: 'resolved' })
})
  .then(res => res.json())
  .then(data => console.log('Updated:', data.success));
```

---

**Last Updated**: June 7, 2026  
**API Version**: 1.0
