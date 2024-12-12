from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel

class BaseState(BaseModel):
    """Base state for graph nodes"""
    timestamp: datetime
    metadata: Dict[str, Any] = {}

class EvolutionState(BaseState):
    """State for evolution tracking"""
    pattern_confidence: float = 0.5
    narrative_consistency: float = 0.5
    prediction_accuracy: float = 0.5
    temporal_connections: Dict[str, float] = {}
    processed_content_ids: List[str] = []

class InteractionState(BaseState):
    """State for interaction management"""
    thread_id: Optional[str] = None
    participants: List[str] = []
    topics: List[str] = []
    sentiment: float = 0.0
    intensity: float = 0.5
    conversation_history: List[Dict[str, Any]] = []