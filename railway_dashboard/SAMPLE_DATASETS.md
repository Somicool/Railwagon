# Sample Datasets Documentation

This document describes the sample datasets included with the rAIlwagon system for demonstration and testing.

---

## 1. Sample Historical Incidents

### Location
```
backend/incidents_db/sample_incidents.json
```

### Overview
5 pre-loaded historical incidents demonstrating various damage types, severities, and resolution patterns. These incidents are automatically loaded when the system starts with an empty database.

### Purpose
- Demonstrate AI recommendation capabilities
- Provide similarity search examples
- Show response time tracking
- Enable immediate testing without data generation

---

### Sample Incident 1: Severe Structural Damage

```json
{
  "id": "INC-20251215093000",
  "type": "wagon_damage",
  "severity": "critical",
  "status": "resolved",
  "title": "Severe structural damage on wagon NR-12345",
  "description": "Critical structural crack detected in main support beam during automated inspection. Crack extends approximately 15cm along load-bearing structure. Immediate safety concern identified requiring urgent response and wagon isolation.",
  "detected_at": "2025-12-15T09:30:00",
  "acknowledged_at": "2025-12-15T09:35:00",
  "resolved_at": "2025-12-15T12:45:00",
  "session_id": "1734252600000",
  "wagon_number": "NR-12345",
  "frame_number": 145,
  "damage_type": "structural",
  "confidence": 0.92,
  "root_cause": "Metal fatigue from prolonged heavy load cycles and age of structural components",
  "resolution_steps": [
    "Wagon immediately isolated from service and quarantined",
    "Emergency maintenance team dispatched within 5 minutes",
    "Complete structural assessment performed",
    "Damaged support beam replaced with reinforced component",
    "Full structural integrity testing completed",
    "Load capacity verification performed",
    "Wagon certified and returned to active service"
  ],
  "assigned_to": "Emergency Response Team A",
  "response_time_minutes": 195.0,
  "similar_incidents": [],
  "recommended_actions": [
    "Immediately isolate affected wagon from service",
    "Dispatch maintenance team for on-site inspection",
    "Document damage with high-resolution photos",
    "Notify safety supervisor and operations manager",
    "Review maintenance logs for affected wagon"
  ],
  "recommended_by_ai": false,
  "image_path": null,
  "notes": [
    "Similar crack pattern observed in fleet analysis",
    "Recommended inspection of wagons from same manufacturing batch"
  ],
  "tags": ["structural", "critical", "beam_failure", "emergency_response"]
}
```

**Learning Points**:
- Critical severity → Immediate isolation
- Fast response time (195 min for critical structural)
- Detailed resolution process
- Preventive recommendations for fleet

---

### Sample Incident 2: Broken Glass Window

```json
{
  "id": "INC-20251220141500",
  "type": "wagon_damage",
  "severity": "high",
  "status": "resolved",
  "title": "Broken glass window detected on wagon NR-23456",
  "description": "Shattered window glass identified on passenger wagon during routine inspection. Large fragments present, safety hazard for passengers. Glass appears to have been impacted by external object.",
  "detected_at": "2025-12-20T14:15:00",
  "acknowledged_at": "2025-12-20T14:20:00",
  "resolved_at": "2025-12-20T16:45:00",
  "session_id": "1734703500000",
  "wagon_number": "NR-23456",
  "frame_number": 89,
  "damage_type": "broken_glass",
  "confidence": 0.88,
  "root_cause": "External impact from trackside debris",
  "resolution_steps": [
    "Wagon removed from passenger service",
    "Glass fragments safely removed and area secured",
    "Window frame inspected for additional damage",
    "Tempered safety glass installed as replacement",
    "Adjacent windows inspected for stress cracks",
    "Wagon cleaned and prepared for service",
    "Safety inspection completed and documented"
  ],
  "assigned_to": "Maintenance Team B",
  "response_time_minutes": 150.0,
  "similar_incidents": [],
  "recommended_actions": [
    "Remove wagon from service immediately",
    "Secure area and remove glass hazards",
    "Schedule window replacement within 24 hours",
    "Inspect adjacent windows for stress damage",
    "Review trackside debris clearance procedures"
  ],
  "recommended_by_ai": false,
  "image_path": null,
  "notes": [
    "Third broken window incident this month",
    "Trackside vegetation control may be inadequate"
  ],
  "tags": ["broken_glass", "safety_hazard", "window", "passenger_wagon"]
}
```

**Learning Points**:
- High severity → Remove from service
- Standard repair procedure established
- Pattern recognition (3rd incident)
- Root cause points to infrastructure issue

---

### Sample Incident 3: OCR Reading Failure

```json
{
  "id": "INC-20251228103000",
  "type": "ocr_failure",
  "severity": "medium",
  "status": "resolved",
  "title": "Unable to read wagon number - OCR failure",
  "description": "Automated OCR system unable to extract wagon identification number from captured frames. Multiple attempts with deblurred images yielded no readable text. Visual inspection suggests heavy dirt/grime coverage obscuring number plate.",
  "detected_at": "2025-12-28T10:30:00",
  "acknowledged_at": "2025-12-28T10:32:00",
  "resolved_at": "2025-12-28T10:45:00",
  "session_id": "1735386600000",
  "wagon_number": "NR-34567",
  "frame_number": 67,
  "damage_type": null,
  "confidence": 0.15,
  "root_cause": "Number plate covered with dirt and grime reducing contrast",
  "resolution_steps": [
    "Manual visual inspection performed",
    "Wagon number identified as NR-34567",
    "Number plate cleaned and photographed",
    "OCR re-run successfully on cleaned plate",
    "Wagon added to cleaning schedule",
    "Database updated with correct identification"
  ],
  "assigned_to": "Inspection Operator - Sarah Johnson",
  "response_time_minutes": 15.0,
  "similar_incidents": [],
  "recommended_actions": [
    "Perform manual visual inspection",
    "Clean number plate and retry OCR",
    "Verify wagon identity through secondary markers",
    "Update OCR training data if new font detected",
    "Schedule regular number plate cleaning maintenance"
  ],
  "recommended_by_ai": false,
  "image_path": null,
  "notes": [
    "Fast resolution due to simple cause",
    "Consider pre-inspection cleaning protocol"
  ],
  "tags": ["ocr_failure", "maintenance", "cleaning", "quick_resolution"]
}
```

**Learning Points**:
- Medium severity → Manual intervention acceptable
- Quick resolution (15 min)
- Process improvement identified
- Pattern suggests systematic cleaning needed

---

### Sample Incident 4: Paint Damage and Corrosion

```json
{
  "id": "INC-20260103080000",
  "type": "wagon_damage",
  "severity": "medium",
  "status": "in_progress",
  "title": "Extensive paint damage and corrosion on wagon NR-45678",
  "description": "Significant paint deterioration observed on wagon exterior with visible rust formation. Corrosion covers approximately 30% of lower side panel. No structural compromise detected but protective coating severely degraded.",
  "detected_at": "2026-01-03T08:00:00",
  "acknowledged_at": "2026-01-03T08:15:00",
  "resolved_at": null,
  "session_id": "1735891200000",
  "wagon_number": "NR-45678",
  "frame_number": 234,
  "damage_type": "paint_damage",
  "confidence": 0.91,
  "root_cause": "Exposure to harsh weather conditions without protective maintenance",
  "resolution_steps": [
    "Wagon scheduled for paint shop treatment",
    "Surface preparation work initiated",
    "Rust treatment application in progress"
  ],
  "assigned_to": "Paint Shop Team",
  "response_time_minutes": null,
  "similar_incidents": [],
  "recommended_actions": [
    "Schedule comprehensive paint restoration",
    "Apply rust inhibitor to affected areas",
    "Inspect structural integrity beneath corrosion",
    "Implement protective coating maintenance schedule",
    "Consider weatherproofing upgrades for fleet"
  ],
  "recommended_by_ai": false,
  "image_path": null,
  "notes": [
    "Work in progress - estimated completion 3-5 days",
    "May require extended workshop time"
  ],
  "tags": ["paint_damage", "corrosion", "cosmetic", "maintenance"]
}
```

**Learning Points**:
- Medium severity → Scheduled maintenance
- In-progress status tracking
- Preventive recommendations for fleet
- Longer resolution timeframe acceptable

---

### Sample Incident 5: Critical Support Beam Crack

```json
{
  "id": "INC-20260105150000",
  "type": "wagon_damage",
  "severity": "critical",
  "status": "resolved",
  "title": "Critical support beam crack detected on wagon NR-56789",
  "description": "Major structural crack discovered in primary support beam during deep inspection. Crack propagation indicates stress fracture with potential for catastrophic failure. Immediate action required to prevent service failure.",
  "detected_at": "2026-01-05T15:00:00",
  "acknowledged_at": "2026-01-05T15:02:00",
  "resolved_at": "2026-01-05T19:30:00",
  "session_id": "1736088000000",
  "wagon_number": "NR-56789",
  "frame_number": 178,
  "damage_type": "structural",
  "confidence": 0.94,
  "root_cause": "Stress fracture from repeated heavy loading beyond design specifications",
  "resolution_steps": [
    "Emergency stop order issued - wagon isolated immediately",
    "Structural engineering team consulted",
    "Load history analysis performed",
    "Complete beam replacement with upgraded component",
    "Enhanced structural monitoring system installed",
    "Load capacity recertification completed",
    "Comprehensive safety check performed",
    "Wagon returned to service with load restrictions"
  ],
  "assigned_to": "Emergency Structural Team",
  "response_time_minutes": 270.0,
  "similar_incidents": ["INC-20251215093000"],
  "recommended_actions": [
    "Immediate service suspension and wagon isolation",
    "Emergency structural engineering assessment",
    "Complete load history review",
    "Beam replacement with enhanced specifications",
    "Implement continuous structural monitoring",
    "Review and adjust load capacity limits"
  ],
  "recommended_by_ai": false,
  "image_path": null,
  "notes": [
    "Second critical structural incident this quarter",
    "Fleet-wide load capacity review recommended",
    "Consider upgrading structural monitoring systems"
  ],
  "tags": ["structural", "critical", "stress_fracture", "emergency", "load_capacity"]
}
```

**Learning Points**:
- Critical severity → Emergency response
- Similar to Incident 1 (beam failure pattern)
- Longest resolution time (270 min) but appropriate for complexity
- Systemic recommendations (fleet-wide review)

---

## 2. AI Learning Demonstration

### Similarity Matrix (Cosine Similarity)

When a new structural damage incident occurs, the AI finds these similarities:

| New Incident | Similar To | Similarity Score | Why Similar |
|--------------|-----------|------------------|-------------|
| Beam crack (new) | INC-20251215093000 | 0.89 | Both structural beam failures |
| Beam crack (new) | INC-20260105150000 | 0.87 | Both critical stress fractures |
| Beam crack (new) | INC-20251220141500 | 0.34 | Both wagon damage (low similarity) |
| Beam crack (new) | INC-20251228103000 | 0.12 | Different types (very low) |

### Recommendation Generation Example

**New Incident**: "Structural crack detected in wagon NR-99999"

**AI Process**:
1. Finds similar incidents: INC-20251215093000 (0.89), INC-20260105150000 (0.87)
2. Extracts resolution steps from both
3. Ranks by frequency × similarity:
   - "Immediately isolate wagon" (appeared 2x, avg similarity 0.88) → **Top recommendation**
   - "Emergency team dispatch" (appeared 2x, avg similarity 0.88)
   - "Structural assessment" (appeared 2x, avg similarity 0.88)
4. Returns top 5 recommendations

**Output**:
```json
{
  "recommended_actions": [
    "Immediate service suspension and wagon isolation",
    "Emergency structural engineering assessment",
    "Complete load history review",
    "Beam replacement with enhanced specifications",
    "Implement continuous structural monitoring"
  ],
  "confidence": 0.88,
  "based_on": 2
}
```

---

## 3. Sample Inspection Session

### Location
```
backend/sessions/1704628800000/
```

### Session Metadata
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
  "wagon_numbers": [
    {"number": "NR-12345", "frame": 45, "confidence": 0.96},
    {"number": "NR-12346", "frame": 89, "confidence": 0.91},
    {"number": "NR-12347", "frame": 123, "confidence": 0.93},
    {"number": "NR-12348", "frame": 156, "confidence": 0.88}
  ],
  "damage_detections": [
    {
      "frame": 145,
      "damage_type": "crack",
      "confidence": 0.87,
      "incident_id": "INC-20260107100730"
    }
  ]
}
```

---

## 4. Response Time Statistics

Based on sample incidents:

| Incident Type | Avg Response Time | Min | Max | Count |
|--------------|-------------------|-----|-----|-------|
| **wagon_damage (critical)** | 232.5 min | 195 | 270 | 2 |
| **wagon_damage (high)** | 150.0 min | 150 | 150 | 1 |
| **wagon_damage (medium)** | N/A (in progress) | - | - | 1 |
| **ocr_failure (medium)** | 15.0 min | 15 | 15 | 1 |

**Key Insights**:
- Critical incidents: ~4 hours average (appropriate for structural repairs)
- High severity: ~2.5 hours (window replacement)
- Medium OCR: ~15 minutes (quick resolution)
- Response time improves as AI learns patterns

---

## 5. Damage Type Distribution

```
Structural Damage: 40% (2/5)
Broken Glass: 20% (1/5)
Paint/Corrosion: 20% (1/5)
OCR Failure: 20% (1/5)
```

---

## 6. Status Distribution

```
Resolved: 80% (4/5)
In Progress: 20% (1/5)
```

---

## 7. Severity Distribution

```
Critical: 40% (2/5)
High: 20% (1/5)
Medium: 40% (2/5)
Low: 0% (0/5)
```

---

## 8. Using Sample Data for Testing

### Test Query 1: Find Structural Damage
```javascript
fetch('/api/incidents?type=wagon_damage&damage_type=structural')
```
**Expected**: Returns 2 incidents (INC-20251215093000, INC-20260105150000)

### Test Query 2: Get Recommendations
```javascript
fetch('/api/incident/INC-20251215093000/recommendations')
```
**Expected**: Returns 5 action items based on similar resolved incidents

### Test Query 3: Response Time Stats
```javascript
fetch('/api/incidents/stats')
```
**Expected**: Returns statistics showing critical incidents avg 232.5 min

### Test Query 4: Find Similar Incidents
```javascript
fetch('/api/incident/INC-20260105150000/similar?top_k=3')
```
**Expected**: Returns INC-20251215093000 with high similarity (both structural)

---

## 9. Extending Sample Data

### Adding New Incidents via API
```bash
curl -X POST http://localhost:5000/api/incident \
  -H "Content-Type: application/json" \
  -d '{
    "type": "wagon_damage",
    "severity": "high",
    "title": "New damage incident",
    "description": "Your description here",
    "wagon_number": "NR-99999"
  }'
```

### Adding New Incidents via Python
```python
from incident_manager import IncidentAIAgent, Incident
from datetime import datetime

agent = IncidentAIAgent()

new_incident = Incident(
    id="",
    type="wagon_damage",
    severity="high",
    status="detected",
    title="Wheel bearing failure on wagon NR-77777",
    description="Excessive heat detected in wheel bearing...",
    detected_at=datetime.now().isoformat(),
    wagon_number="NR-77777",
    damage_type="mechanical",
    confidence=0.85
)

incident_id = agent.add_incident(new_incident)
print(f"Created: {incident_id}")
```

---

## 10. Data Reset

To reset to original sample data:

```bash
# Backup current data
cp backend/incidents_db/incidents.json backup/incidents_backup.json

# Restore samples
cp backend/incidents_db/sample_incidents.json backend/incidents_db/incidents.json

# Delete embeddings (will be regenerated)
rm backend/incidents_db/embeddings.npy

# Restart server
python backend/app.py
```

---

**Last Updated**: June 7, 2026  
**Sample Data Version**: 1.0
