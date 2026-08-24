"""
AI-Powered Incident Management System
======================================
Integrates with railway inspection system to capture, classify, and resolve incidents.
Uses vector embeddings and similarity search to recommend solutions from past incidents.

Author: Railway Wagon Inspection AI Team
Date: January 2026
"""

import json
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import torch
from dataclasses import dataclass, asdict, field
from enum import Enum

# Lazy imports for performance
_sentence_transformer = None
_faiss = None

def get_sentence_transformer():
    """Lazy load sentence transformer"""
    global _sentence_transformer
    if _sentence_transformer is None:
        from sentence_transformers import SentenceTransformer
        print("[INCIDENT AI] Loading embedding model: all-MiniLM-L6-v2")
        _sentence_transformer = SentenceTransformer('all-MiniLM-L6-v2')
    return _sentence_transformer

def get_faiss():
    """Lazy load FAISS"""
    global _faiss
    if _faiss is None:
        import faiss
        _faiss = faiss
    return _faiss


class IncidentSeverity(Enum):
    CRITICAL = "critical"  # Structural damage, immediate safety risk
    HIGH = "high"          # Broken glass, major component failure
    MEDIUM = "medium"      # Cracks, minor damage
    LOW = "low"            # Cosmetic issues, warnings


class IncidentStatus(Enum):
    DETECTED = "detected"
    ACKNOWLEDGED = "acknowledged"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    ESCALATED = "escalated"


class IncidentType(Enum):
    WAGON_DAMAGE = "wagon_damage"
    OCR_FAILURE = "ocr_failure"
    SYSTEM_ERROR = "system_error"
    QUALITY_ISSUE = "quality_issue"


@dataclass
class Incident:
    id: str
    type: str  # Use string instead of Enum for JSON serialization
    severity: str
    status: str
    title: str
    description: str
    detected_at: str
    acknowledged_at: Optional[str] = None
    resolved_at: Optional[str] = None
    
    # Detection details
    session_id: str = ""
    wagon_number: Optional[str] = None
    frame_number: Optional[int] = None
    damage_type: Optional[str] = None
    confidence: float = 0.0
    
    # Resolution tracking
    root_cause: Optional[str] = None
    resolution_steps: List[str] = field(default_factory=list)
    assigned_to: Optional[str] = None
    response_time_minutes: Optional[float] = None
    
    # AI recommendations
    similar_incidents: List[str] = field(default_factory=list)
    recommended_actions: List[str] = field(default_factory=list)
    recommended_by_ai: bool = False
    
    # Metadata
    image_path: Optional[str] = None
    notes: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)


class IncidentAIAgent:
    """AI agent that learns from past incidents and recommends solutions"""
    
    def __init__(self, db_path: str = "incidents_db"):
        self.db_path = Path(db_path)
        self.db_path.mkdir(exist_ok=True)
        
        self.incidents_file = self.db_path / "incidents.json"
        self.embeddings_file = self.db_path / "embeddings.npy"
        
        # Lazy load models
        self._embedding_model = None
        self._embedding_dim = None
        
        # Load incidents database
        self.incidents: List[Incident] = []
        self.embeddings: np.ndarray = np.array([])
        self.index = None
        
        self._load_database()
        print(f"[INCIDENT AI] Loaded {len(self.incidents)} historical incidents")
        
        # Load sample incidents if database is empty
        if len(self.incidents) == 0:
            self._load_sample_incidents()
    
    @property
    def embedding_model(self):
        """Lazy load embedding model"""
        if self._embedding_model is None:
            self._embedding_model = get_sentence_transformer()
            self._embedding_dim = self._embedding_model.get_sentence_embedding_dimension()
        return self._embedding_model
    
    @property
    def embedding_dim(self):
        """Get embedding dimension"""
        if self._embedding_dim is None:
            _ = self.embedding_model  # Trigger lazy load
        return self._embedding_dim
    
    def _load_database(self):
        """Load incidents and embeddings from disk"""
        if self.incidents_file.exists():
            try:
                with open(self.incidents_file, 'r') as f:
                    data = json.load(f)
                    self.incidents = [Incident(**item) for item in data]
            except Exception as e:
                print(f"[INCIDENT AI] Error loading incidents: {e}")
                self.incidents = []
        
        if self.embeddings_file.exists():
            try:
                self.embeddings = np.load(self.embeddings_file)
                if len(self.embeddings) > 0:
                    faiss = get_faiss()
                    self.index = faiss.IndexFlatL2(self.embeddings.shape[1])
                    self.index.add(self.embeddings.astype(np.float32))
            except Exception as e:
                print(f"[INCIDENT AI] Error loading embeddings: {e}")
                self.embeddings = np.array([])
    
    def _load_sample_incidents(self):
        """Load sample incidents for demonstration"""
        sample_file = self.db_path / "sample_incidents.json"
        if sample_file.exists():
            try:
                with open(sample_file, 'r') as f:
                    data = json.load(f)
                    for item in data:
                        incident = Incident(**item)
                        self.add_incident(incident)
                print(f"[INCIDENT AI] Loaded {len(data)} sample incidents")
            except Exception as e:
                print(f"[INCIDENT AI] Error loading sample incidents: {e}")
    
    def _save_database(self):
        """Save incidents and embeddings to disk"""
        try:
            with open(self.incidents_file, 'w') as f:
                json.dump([asdict(inc) for inc in self.incidents], f, indent=2)
            
            if len(self.embeddings) > 0:
                np.save(self.embeddings_file, self.embeddings)
        except Exception as e:
            print(f"[INCIDENT AI] Error saving database: {e}")
    
    def _create_incident_text(self, incident: Incident) -> str:
        """Create searchable text representation of incident"""
        parts = [
            f"Type: {incident.type}",
            f"Severity: {incident.severity}",
            f"Title: {incident.title}",
            f"Description: {incident.description}",
        ]
        
        if incident.damage_type:
            parts.append(f"Damage: {incident.damage_type}")
        if incident.root_cause:
            parts.append(f"Root Cause: {incident.root_cause}")
        if incident.resolution_steps:
            parts.append(f"Resolution: {' '.join(incident.resolution_steps)}")
        
        return " | ".join(parts)
    
    def add_incident(self, incident: Incident) -> str:
        """Add new incident to database and compute embedding"""
        # Assign ID if not present
        if not incident.id:
            incident.id = f"INC-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Create embedding
        incident_text = self._create_incident_text(incident)
        embedding = self.embedding_model.encode([incident_text])[0]
        
        # Add to database
        self.incidents.append(incident)
        
        # Add to FAISS index
        faiss = get_faiss()
        if self.index is None:
            self.index = faiss.IndexFlatL2(self.embedding_dim)
        
        self.index.add(np.array([embedding], dtype=np.float32))
        
        # Update embeddings array
        if len(self.embeddings) == 0:
            self.embeddings = np.array([embedding], dtype=np.float32)
        else:
            self.embeddings = np.vstack([self.embeddings, embedding])
        
        self._save_database()
        print(f"[INCIDENT AI] Added incident {incident.id}")
        return incident.id
    
    def find_similar_incidents(self, incident: Incident, top_k: int = 5) -> List[Dict]:
        """Find similar past incidents using vector similarity"""
        if len(self.incidents) == 0 or self.index is None:
            return []
        
        # Create embedding for current incident
        incident_text = self._create_incident_text(incident)
        query_embedding = self.embedding_model.encode([incident_text])[0]
        query_embedding = np.array([query_embedding], dtype=np.float32)
        
        # Search FAISS index
        k = min(top_k, len(self.incidents))
        distances, indices = self.index.search(query_embedding, k)
        
        # Return similar incidents with similarity scores
        results = []
        for i, (dist, idx) in enumerate(zip(distances[0], indices[0])):
            if idx < len(self.incidents):
                similar_incident = self.incidents[idx]
                similarity_score = 1 / (1 + dist)  # Convert distance to similarity
                
                results.append({
                    'incident': asdict(similar_incident),
                    'similarity_score': float(similarity_score),
                    'rank': i + 1
                })
        
        return results
    
    def recommend_actions(self, incident: Incident) -> List[str]:
        """Recommend resolution actions based on similar past incidents"""
        similar = self.find_similar_incidents(incident, top_k=5)
        
        if not similar:
            return self._get_default_recommendations(incident)
        
        # Extract resolution steps from similar incidents
        recommended_actions = []
        action_counts = {}
        
        for item in similar:
            past_incident = Incident(**item['incident'])
            if past_incident.status == 'resolved' and past_incident.resolution_steps:
                for step in past_incident.resolution_steps:
                    action_counts[step] = action_counts.get(step, 0) + item['similarity_score']
        
        # Sort by frequency and similarity
        sorted_actions = sorted(action_counts.items(), key=lambda x: x[1], reverse=True)
        recommended_actions = [action for action, score in sorted_actions[:5]]
        
        # Add default recommendations if needed
        if len(recommended_actions) < 3:
            default_actions = self._get_default_recommendations(incident)
            for action in default_actions:
                if action not in recommended_actions:
                    recommended_actions.append(action)
        
        return recommended_actions[:5]
    
    def _get_default_recommendations(self, incident: Incident) -> List[str]:
        """Get default recommendations based on incident type and severity"""
        recommendations = []
        
        if incident.type == 'wagon_damage':
            if incident.severity in ['critical', 'high']:
                recommendations.extend([
                    "Immediately isolate affected wagon from service",
                    "Dispatch maintenance team for on-site inspection",
                    "Document damage with high-resolution photos",
                    "Notify safety supervisor and operations manager",
                    "Review maintenance logs for affected wagon"
                ])
            else:
                recommendations.extend([
                    "Schedule routine maintenance inspection",
                    "Add wagon to repair queue",
                    "Document damage details for maintenance records"
                ])
        
        elif incident.type == 'ocr_failure':
            recommendations.extend([
                "Verify wagon number manually from frame",
                "Check image quality and lighting conditions",
                "Re-run OCR with enhanced deblurring",
                "Update OCR training data if pattern not recognized"
            ])
        
        elif incident.type == 'system_error':
            recommendations.extend([
                "Check system logs for error details",
                "Verify model weights and dependencies",
                "Restart inspection service if needed",
                "Contact system administrator if error persists"
            ])
        
        return recommendations
    
    def get_response_time_stats(self) -> Dict:
        """Calculate average response times for different incident types"""
        stats = {}
        
        for incident_type in ['wagon_damage', 'ocr_failure', 'system_error', 'quality_issue']:
            relevant_incidents = [
                inc for inc in self.incidents
                if inc.type == incident_type and inc.response_time_minutes is not None
            ]
            
            if relevant_incidents:
                response_times = [inc.response_time_minutes for inc in relevant_incidents]
                stats[incident_type] = {
                    'avg_response_time': float(np.mean(response_times)),
                    'min_response_time': float(np.min(response_times)),
                    'max_response_time': float(np.max(response_times)),
                    'count': len(relevant_incidents)
                }
        
        return stats
    
    def get_incident_by_id(self, incident_id: str) -> Optional[Incident]:
        """Retrieve incident by ID"""
        for incident in self.incidents:
            if incident.id == incident_id:
                return incident
        return None
    
    def update_incident(self, incident_id: str, updates: Dict) -> bool:
        """Update existing incident"""
        for i, incident in enumerate(self.incidents):
            if incident.id == incident_id:
                # Update fields
                for key, value in updates.items():
                    if hasattr(incident, key):
                        setattr(incident, key, value)
                
                # Calculate response time if resolved
                if incident.status == 'resolved' and incident.resolved_at:
                    try:
                        detected = datetime.fromisoformat(incident.detected_at)
                        resolved = datetime.fromisoformat(incident.resolved_at)
                        incident.response_time_minutes = (resolved - detected).total_seconds() / 60
                    except:
                        pass
                
                self._save_database()
                return True
        return False


# Damage severity mapping
DAMAGE_SEVERITY_MAP = {
    'structural': 'critical',
    'broken_glass': 'high',
    'broken': 'high',
    'crack': 'medium',
    'scratch': 'low',
    'dent': 'medium',
}


def create_incident_from_damage_detection(
    damage_result: Dict,
    session_id: str,
    frame_number: int,
    wagon_number: Optional[str] = None
) -> Incident:
    """Create incident from damage detection result"""
    
    damage_type = damage_result.get('damage_type', 'unknown')
    confidence = damage_result.get('confidence', 0.0)
    damage_count = damage_result.get('damage_count', 0)
    
    # Determine severity
    severity = DAMAGE_SEVERITY_MAP.get(damage_type, 'medium')
    
    # Adjust severity based on confidence
    if confidence < 0.6:
        severity = 'low'
    
    # Create title and description
    title = f"{damage_type.title()} Damage Detected on Wagon"
    if wagon_number:
        title += f" {wagon_number}"
    
    description = f"""
Damage detected during automated inspection.
- Damage Type: {damage_type}
- Confidence: {confidence:.2%}
- Number of Damaged Areas: {damage_count}
- Frame Number: {frame_number}
- Session ID: {session_id}
    """.strip()
    
    # Create incident
    incident = Incident(
        id="",  # Will be assigned by AI agent
        type='wagon_damage',
        severity=severity,
        status='detected',
        title=title,
        description=description,
        detected_at=datetime.now().isoformat(),
        session_id=session_id,
        wagon_number=wagon_number,
        frame_number=frame_number,
        damage_type=damage_type,
        confidence=confidence,
        tags=[damage_type, 'automated_detection']
    )
    
    return incident
