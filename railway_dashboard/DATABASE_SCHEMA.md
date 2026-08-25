# Database Schema Documentation

## Overview
The rAIlwagon system uses a **file-based database** with JSON storage and NumPy arrays for vector embeddings. This design provides simplicity, portability, and offline capability.

---

## 1. Incidents Database

### Storage Location
```
backend/incidents_db/
├── incidents.json          # Main incident records
├── embeddings.npy          # Vector embeddings (384-dim)
└── sample_incidents.json   # Pre-loaded sample data
```

### Schema: Incident Record

```json
{
  "id": "string (INC-YYYYMMDDHHmmss)",
  "type": "string (enum)",
  "severity": "string (enum)",
  "status": "string (enum)",
  "title": "string",
  "description": "string (detailed)",
  
  "detected_at": "ISO 8601 datetime",
  "acknowledged_at": "ISO 8601 datetime | null",
  "resolved_at": "ISO 8601 datetime | null",
  
  "session_id": "string",
  "wagon_number": "string | null",
  "frame_number": "integer | null",
  "damage_type": "string | null",
  "confidence": "float (0.0-1.0)",
  
  "root_cause": "string | null",
  "resolution_steps": ["string array"],
  "assigned_to": "string | null",
  "response_time_minutes": "float | null",
  
  "similar_incidents": ["string array of incident IDs"],
  "recommended_actions": ["string array"],
  "recommended_by_ai": "boolean",
  
  "image_path": "string | null",
  "notes": ["string array"],
  "tags": ["string array"]
}
```

### Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique identifier (auto-generated) |
| `type` | enum | Yes | wagon_damage, ocr_failure, system_error, quality_issue |
| `severity` | enum | Yes | critical, high, medium, low |
| `status` | enum | Yes | detected, acknowledged, in_progress, resolved, escalated |
| `title` | string | Yes | Brief incident description |
| `description` | string | Yes | Detailed incident information |
| `detected_at` | datetime | Yes | When incident was first detected |
| `acknowledged_at` | datetime | No | When operator acknowledged |
| `resolved_at` | datetime | No | When incident was resolved |
| `session_id` | string | No | Associated inspection session |
| `wagon_number` | string | No | Railway wagon identifier |
| `frame_number` | integer | No | Video frame where detected |
| `damage_type` | string | No | structural, broken_glass, crack, scratch, dent |
| `confidence` | float | No | Detection confidence (0.0-1.0) |
| `root_cause` | string | No | Identified cause of incident |
| `resolution_steps` | array | No | Steps taken to resolve |
| `assigned_to` | string | No | Person/team assigned |
| `response_time_minutes` | float | No | Time from detection to resolution |
| `similar_incidents` | array | No | IDs of similar past incidents |
| `recommended_actions` | array | No | AI-generated recommendations |
| `recommended_by_ai` | boolean | No | Whether AI provided recommendations |
| `image_path` | string | No | Path to associated image |
| `notes` | array | No | Additional operator notes |
| `tags` | array | No | Custom tags for filtering |

### Example Record

```json
{
  "id": "INC-20260107120000",
  "type": "wagon_damage",
  "severity": "critical",
  "status": "resolved",
  "title": "Severe structural damage on wagon NR-12345",
  "description": "Cracked support beam detected during automated inspection. Crack extends 15cm along main load-bearing beam. Immediate action required.",
  
  "detected_at": "2026-01-07T12:00:00",
  "acknowledged_at": "2026-01-07T12:05:00",
  "resolved_at": "2026-01-07T14:30:00",
  
  "session_id": "1704628800000",
  "wagon_number": "NR-12345",
  "frame_number": 145,
  "damage_type": "structural",
  "confidence": 0.92,
  
  "root_cause": "Metal fatigue due to age and heavy load cycles",
  "resolution_steps": [
    "Wagon immediately isolated from service",
    "Emergency maintenance team dispatched",
    "Support beam replaced with reinforced model",
    "Full structural integrity test completed",
    "Wagon certified and returned to service"
  ],
  "assigned_to": "Maintenance Team A - Senior Engineer",
  "response_time_minutes": 150.0,
  
  "similar_incidents": ["INC-20251215093000", "INC-20251120141500"],
  "recommended_actions": [
    "Immediately isolate affected wagon from service",
    "Dispatch maintenance team for on-site inspection",
    "Document damage with high-resolution photos",
    "Notify safety supervisor and operations manager",
    "Review maintenance logs for affected wagon"
  ],
  "recommended_by_ai": true,
  
  "image_path": "/sessions/1704628800000/wagon_detections/damage_145.jpg",
  "notes": [
    "Similar damage pattern seen in wagon NR-11234 last month",
    "Recommended inspection of all wagons manufactured in same batch"
  ],
  "tags": ["structural", "critical", "beam_failure", "batch_2023"]
}
```

### Enums

**Type Enum**:
```python
WAGON_DAMAGE = "wagon_damage"      # Physical damage to wagon
OCR_FAILURE = "ocr_failure"        # Unable to read wagon number
SYSTEM_ERROR = "system_error"      # Software/hardware malfunction
QUALITY_ISSUE = "quality_issue"    # Image quality problems
```

**Severity Enum**:
```python
CRITICAL = "critical"  # Immediate safety risk, service disruption
HIGH = "high"          # Major component failure, urgent action needed
MEDIUM = "medium"      # Significant issue, schedule repair soon
LOW = "low"            # Minor issue, routine maintenance
```

**Status Enum**:
```python
DETECTED = "detected"          # Newly detected, awaiting review
ACKNOWLEDGED = "acknowledged"  # Operator has seen and acknowledged
IN_PROGRESS = "in_progress"    # Currently being worked on
RESOLVED = "resolved"          # Issue fixed and verified
ESCALATED = "escalated"        # Elevated to higher authority
```

---

## 2. Vector Embeddings Database

### Storage Location
```
backend/incidents_db/embeddings.npy
```

### Schema
- **Format**: NumPy array (.npy file)
- **Dimensions**: `[N, 384]` where N = number of incidents
- **Data Type**: `float32`
- **Index Alignment**: Row `i` corresponds to incident `i` in incidents.json

### Structure
```python
embeddings = np.array([
    [0.123, -0.456, 0.789, ...],  # Incident 0 embedding (384 dims)
    [0.234, -0.567, 0.890, ...],  # Incident 1 embedding (384 dims)
    ...
], dtype=np.float32)
```

### Generation Process
1. Concatenate incident fields: `type | severity | title | description | damage_type | root_cause | resolution_steps`
2. Pass through Sentence-BERT model (all-MiniLM-L6-v2)
3. Generate 384-dimensional dense vector
4. Store in embeddings.npy aligned with incidents.json

### FAISS Index
- **Type**: `IndexFlatL2` (exact L2 distance search)
- **Metric**: Euclidean distance (L2)
- **Conversion to Similarity**: `similarity = 1 / (1 + distance)`
- **Rebuilt**: On server startup from embeddings.npy

---

## 3. Inspection Sessions Database

### Storage Location
```
backend/sessions/<session_id>/
├── metadata.json           # Session information
├── frames/                 # Original captured frames
│   ├── frame_0000.jpg
│   ├── frame_0001.jpg
│   └── ...
├── deblurred/             # Deblurred frames
│   ├── deblurred_0000.jpg
│   ├── deblurred_0001.jpg
│   └── ...
└── wagon_detections/      # Detected wagons and damage
    ├── wagon_NR-12345_145.jpg
    ├── damage_145.jpg
    └── ...
```

### Schema: Session Metadata

```json
{
  "id": "string (Unix timestamp milliseconds)",
  "type": "string (live | recorded)",
  "operator": "string",
  "start_time": "ISO 8601 datetime",
  "end_time": "ISO 8601 datetime",
  "status": "string (running | completed | error)",
  
  "results": {
    "frames_processed": "integer",
    "wagons_detected": "integer",
    "damage_incidents": "integer",
    "ocr_success_rate": "float (0.0-1.0)",
    "average_fps": "float",
    "total_duration_seconds": "float"
  },
  
  "settings": {
    "use_motion_detection": "boolean",
    "motion_threshold": "float",
    "video_source": "string | integer"
  },
  
  "wagon_numbers": [
    {
      "number": "string",
      "frame": "integer",
      "confidence": "float",
      "timestamp": "ISO 8601 datetime"
    }
  ],
  
  "damage_detections": [
    {
      "frame": "integer",
      "damage_type": "string",
      "confidence": "float",
      "bbox": [x, y, width, height],
      "incident_id": "string (INC-...)"
    }
  ],
  
  "archived": "boolean",
  "archived_at": "ISO 8601 datetime | null"
}
```

### Example Session Record

```json
{
  "id": "1704628800000",
  "type": "live",
  "operator": "John Smith",
  "start_time": "2026-01-07T10:00:00",
  "end_time": "2026-01-07T10:15:30",
  "status": "completed",
  
  "results": {
    "frames_processed": 245,
    "wagons_detected": 12,
    "damage_incidents": 3,
    "ocr_success_rate": 0.95,
    "average_fps": 15.8,
    "total_duration_seconds": 930
  },
  
  "settings": {
    "use_motion_detection": true,
    "motion_threshold": 15.0,
    "video_source": 0
  },
  
  "wagon_numbers": [
    {
      "number": "NR-12345",
      "frame": 45,
      "confidence": 0.96,
      "timestamp": "2026-01-07T10:02:15"
    },
    {
      "number": "NR-12346",
      "frame": 89,
      "confidence": 0.91,
      "timestamp": "2026-01-07T10:05:30"
    }
  ],
  
  "damage_detections": [
    {
      "frame": 145,
      "damage_type": "structural",
      "confidence": 0.92,
      "bbox": [120, 340, 450, 280],
      "incident_id": "INC-20260107120000"
    }
  ],
  
  "archived": false,
  "archived_at": null
}
```

---

## 4. Sample Incidents Database

### Storage Location
```
backend/incidents_db/sample_incidents.json
```

### Purpose
Pre-loaded historical incidents for demonstration and testing. Automatically loaded if main database is empty.

### Schema
Same as main incidents.json (array of Incident objects)

### Included Samples (5 incidents)
1. Severe structural damage (critical, resolved)
2. Broken glass incident (high, resolved)
3. OCR failure case (medium, resolved)
4. Paint damage/corrosion (medium, in_progress)
5. Critical support beam crack (critical, resolved)

---

## 5. Database Operations

### Create Incident
```python
from incident_manager import IncidentAIAgent, Incident

agent = IncidentAIAgent(db_path="incidents_db")

incident = Incident(
    id="",  # Auto-generated
    type="wagon_damage",
    severity="high",
    status="detected",
    title="Broken window on wagon NR-45678",
    description="Shattered glass detected...",
    detected_at=datetime.now().isoformat(),
    wagon_number="NR-45678",
    confidence=0.87
)

incident_id = agent.add_incident(incident)
# Auto-generates embedding and adds to FAISS index
```

### Find Similar Incidents
```python
similar = agent.find_similar_incidents(incident, top_k=5)

for item in similar:
    print(f"Similar: {item['incident']['title']}")
    print(f"Similarity: {item['similarity_score']:.2f}")
    print(f"Rank: {item['rank']}")
```

### Get Recommendations
```python
recommendations = agent.recommend_actions(incident)

for action in recommendations:
    print(f"• {action}")
```

### Update Incident
```python
agent.update_incident(incident_id, {
    "status": "resolved",
    "resolved_at": datetime.now().isoformat(),
    "root_cause": "Impact damage from debris",
    "resolution_steps": [
        "Window replaced",
        "Area inspected",
        "Wagon cleared for service"
    ]
})
# Auto-calculates response_time_minutes
```

---

## 6. Data Relationships

```
Inspection Session (1) ────> (N) Frames
                     │
                     └────> (N) Wagon Detections
                     │
                     └────> (N) Damage Detections
                                    │
                                    └────> (1) Incident
                                              │
                                              └────> (N) Similar Incidents
                                              │
                                              └────> (1) Embedding Vector
```

---

## 7. Indexing Strategy

### Primary Keys
- **Incidents**: `id` (string, auto-generated)
- **Sessions**: `id` (Unix timestamp)
- **Embeddings**: Array index (matches incident array position)

### Search Optimization
- **Vector Search**: FAISS IndexFlatL2 (exact search)
- **Status Filter**: In-memory filtering in Python
- **Date Range**: ISO 8601 string comparison

### Performance Characteristics
- **Add Incident**: O(1) append + O(N) for embedding + O(N) for FAISS add
- **Find Similar**: O(N) FAISS search (exact), O(log N) with IVF indices
- **Get by ID**: O(N) linear search (consider hash map for >1000 incidents)
- **Filter**: O(N) linear scan

---

## 8. Backup & Recovery

### Backup Strategy
```bash
# Manual backup
cp -r backend/incidents_db/ backup/incidents_db_$(date +%Y%m%d)/
cp -r backend/sessions/ backup/sessions_$(date +%Y%m%d)/
```

### Recovery
```bash
# Restore from backup
cp -r backup/incidents_db_20260107/ backend/incidents_db/
cp -r backup/sessions_20260107/ backend/sessions/
```

### Database Rebuild
```python
# Rebuild embeddings from incidents.json
from incident_manager import IncidentAIAgent
import json

agent = IncidentAIAgent()
agent.embeddings = np.array([])
agent.index = None

with open('incidents.json', 'r') as f:
    incidents = json.load(f)

for inc_data in incidents:
    incident = Incident(**inc_data)
    agent.add_incident(incident)  # Regenerates embeddings
```

---

## 9. Scalability Considerations

### Current Capacity
- **Incidents**: Handles 10,000+ with good performance
- **Sessions**: Unlimited (file-based storage)
- **Embeddings**: Limited by RAM (~400MB for 1M incidents)

### Migration Path to Production DB
For >100,000 incidents, consider:
- **PostgreSQL** with pgvector extension for embeddings
- **MongoDB** for JSON document storage
- **Dedicated Vector DB**: Pinecone, Weaviate, or Milvus
- **Caching Layer**: Redis for frequently accessed data

---

## 10. Data Validation

### Incident Validation
```python
def validate_incident(incident):
    assert incident.type in ["wagon_damage", "ocr_failure", "system_error", "quality_issue"]
    assert incident.severity in ["critical", "high", "medium", "low"]
    assert incident.status in ["detected", "acknowledged", "in_progress", "resolved", "escalated"]
    assert 0.0 <= incident.confidence <= 1.0
    assert len(incident.title) > 0
    assert len(incident.description) > 10
```

### Schema Evolution
For backward compatibility, add new fields with default values:
```python
incident_data.setdefault("new_field", default_value)
```

---

**Last Updated**: June 7, 2026  
**Schema Version**: 1.0
