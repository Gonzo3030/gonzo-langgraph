"""Contextual pattern detection with dynamic knowledge updating."""

from typing import Dict, List, Optional, Set, Any, Tuple
from datetime import datetime, UTC
from uuid import UUID
import logging
from enum import Enum

from ..memory.vector_store import VectorStoreMemory
from ..memory.timeline import Timeline
from ..persistence.checkpointer import Checkpointer
from ..persistence.store import Store
from ..state_management.api_state import APIState

logger = logging.getLogger(__name__)

class ConfidenceLevel(float, Enum):
    """Confidence levels for knowledge claims."""
    LOW = 0.3
    MEDIUM = 0.6
    HIGH = 0.9

class KnowledgeClaim:
    """Represents a piece of knowledge with source and confidence."""
    
    def __init__(self, 
        value: Any,
        source: str,
        confidence: float,
        timestamp: datetime = None
    ):
        self.value = value
        self.source = source
        self.confidence = confidence
        self.timestamp = timestamp or datetime.now(UTC)
        self.corroborations: List[Tuple[str, float]] = []  # (source, confidence)
        
    def add_corroboration(self, source: str, confidence: float) -> None:
        """Add a corroborating source."""
        self.corroborations.append((source, confidence))
        # Update overall confidence based on corroboration
        max_boost = 0.1 * len(self.corroborations)  # Max 10% boost per corroboration
        self.confidence = min(1.0, self.confidence + max_boost)
        
    def to_memory_entry(self) -> Dict[str, Any]:
        """Convert to format suitable for vector store."""
        return {
            "text": str(self.value),
            "metadata": {
                "source": self.source,
                "confidence": self.confidence,
                "timestamp": self.timestamp,
                "corroborations": self.corroborations
            }
        }