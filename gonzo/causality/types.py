from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set
from datetime import datetime
from enum import Enum

class EventCategory(Enum):
    """Categories of events Gonzo tracks."""
    CRYPTO = "crypto"
    FINANCIAL = "financial"
    TECH = "tech"
    SOCIAL = "social"
    POLITICAL = "political"
    WAR = "war"
    ENVIRONMENTAL = "environmental"
    CORPORATE = "corporate"

class EventScope(Enum):
    """Scope/scale of the event's impact."""
    LOCAL = "local"
    REGIONAL = "regional"
    NATIONAL = "national"
    GLOBAL = "global"
    SYSTEMIC = "systemic"  # Changes that affect entire systems

@dataclass
class CausalEvent:
    """An event that's part of a causal chain."""
    id: str  # Unique identifier
    timestamp: datetime
    description: str
    category: EventCategory
    scope: EventScope
    causes: Set[str] = field(default_factory=set)  # IDs of causal events
    effects: Set[str] = field(default_factory=set)  # IDs of effect events
    importance: float = 1.0  # 0-1 scale of historical significance
    confidence: float = 1.0  # How confident we are about this chain
    metadata: Dict = field(default_factory=dict)  # Additional event data

    def add_cause(self, event_id: str) -> None:
        """Add a causal event ID."""
        self.causes.add(event_id)

    def add_effect(self, event_id: str) -> None:
        """Add an effect event ID."""
        self.effects.add(event_id)

@dataclass
class TimelineChain:
    """A sequence of causally linked events leading to a future outcome."""
    id: str
    name: str
    description: str
    events: List[CausalEvent]
    final_outcome: str  # The ultimate result in 3030
    prevention_points: List[datetime]  # Key intervention moments
    warning_signs: List[str]  # Present-day indicators
    categories: Set[EventCategory] = field(default_factory=set)
    
    def __post_init__(self):
        # Auto-populate categories from events
        self.categories = {event.category for event in self.events}

@dataclass
class CausalAnalysis:
    """Result of analyzing current events against known chains."""
    current_event: str
    timestamp: datetime
    historical_parallels: List[CausalEvent]
    matched_chains: List[TimelineChain]
    warnings: List[str]
    prevention_strategies: List[str]
    confidence: float
    metadata: Dict = field(default_factory=dict)