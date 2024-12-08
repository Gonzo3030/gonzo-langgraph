from typing import List, Dict, Any
from datetime import datetime
from langgraph.graph import StateGraph

class Timeline:
    """Graph-aware timeline for event tracking and analysis."""
    
    def __init__(self):
        self._memory = TimelineMemory()
        self._graph_state = None
    
    def add_event(self, event: Dict[str, Any]):
        """Add a new event to the timeline."""
        if not isinstance(event, dict):
            raise ValueError("Event must be a dictionary")
            
        if "timestamp" not in event:
            event["timestamp"] = datetime.utcnow()
            
        self._memory.add_event(
            event=event["type"],
            timestamp=event["timestamp"],
            metadata={k: v for k, v in event.items() if k not in ["type", "timestamp"]}
        )
    
    def get_events(self, limit: int = None) -> List[Dict[str, Any]]:
        """Get timeline events."""
        events = self._memory.get_recent_events(limit=limit if limit else None)
        return [{
            "type": e["event"],
            "timestamp": e["timestamp"],
            **e["metadata"]
        } for e in events]
    
    def to_checkpoint(self) -> Dict[str, Any]:
        """Convert timeline state to checkpoint format."""
        return {
            "events": self._memory.timeline
        }
    
    def from_checkpoint(self, checkpoint: Dict[str, Any]):
        """Restore timeline state from checkpoint."""
        self._memory.timeline = checkpoint.get("events", [])

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
    
    def get_recent_events(self, limit: int = None) -> List[Dict[str, Any]]:
        """Get the most recent events."""
        sorted_events = sorted(
            self.timeline,
            key=lambda x: x["timestamp"],
            reverse=True
        )
        return sorted_events[:limit] if limit else sorted_events
    
    def clear(self):
        """Clear all events."""
        self.timeline = []