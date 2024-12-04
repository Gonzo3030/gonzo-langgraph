from typing import List, Dict, Any
from datetime import datetime

class TimelineMemory:
    """Maintains a timeline of events and predictions."""
    
    def __init__(self):
        self.timeline: List[Dict[str, Any]] = []
    
    def add_event(self, event: str, timestamp: datetime = None, metadata: Dict[str, Any] = None):
        """Add a new event to the timeline."""
        self.timeline.append({
            "event": event,
            "timestamp": timestamp or datetime.utcnow(),
            "metadata": metadata or {}
        })
    
    def get_recent_events(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get the most recent events."""
        return sorted(
            self.timeline,
            key=lambda x: x["timestamp"],
            reverse=True
        )[:limit]
    
    def clear(self):
        """Clear all events."""
        self.timeline = []