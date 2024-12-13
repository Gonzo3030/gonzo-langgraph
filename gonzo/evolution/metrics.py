"""Evolution metrics for tracking system growth."""

from typing import Dict, Any
from pydantic import BaseModel
from datetime import datetime

class EvolutionMetrics(BaseModel):
    """Tracks evolution metrics."""
    pattern_confidence: float = 0.5
    narrative_consistency: float = 0.5
    prediction_accuracy: float = 0.5
    temporal_connections: Dict[str, float] = {}
    timestamp: datetime = None
    
    def __init__(self, **data):
        super().__init__(**data)
        if self.timestamp is None:
            self.timestamp = datetime.now()
            
    @classmethod
    def create_default(cls) -> 'EvolutionMetrics':
        """Create default metrics instance."""
        return cls(
            pattern_confidence=0.5,
            narrative_consistency=0.5,
            prediction_accuracy=0.5,
            temporal_connections={},
            timestamp=datetime.now()
        )
            
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            'pattern_confidence': self.pattern_confidence,
            'narrative_consistency': self.narrative_consistency,
            'prediction_accuracy': self.prediction_accuracy,
            'temporal_connections': self.temporal_connections,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }
        
    def __iter__(self):
        """Make metrics iterable."""
        yield from self.to_dict().items()