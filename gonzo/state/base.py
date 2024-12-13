"""Core state management for Gonzo."""

from typing import List, Dict, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field

class MemoryState(BaseModel):
    """State for memory management"""
    short_term: Dict[str, Any] = Field(default_factory=dict)
    long_term: Dict[str, Any] = Field(default_factory=dict)
    errors: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.now)

class MessageState(BaseModel):
    """State for managing messages and current context"""
    messages: List[str] = Field(default_factory=list)
    current_message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)

class AnalysisState(BaseModel):
    """State for pattern detection and analysis"""
    patterns: List[Dict[str, Any]] = Field(default_factory=list)
    entities: List[Dict[str, str]] = Field(default_factory=list)
    significance: float = 0.0
    temporal_connections: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)

class EvolutionState(BaseModel):
    """State for tracking system evolution"""
    pattern_confidence: float = 0.5
    narrative_consistency: float = 0.5
    prediction_accuracy: float = 0.5
    processed_content_ids: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.now)

class InteractionState(BaseModel):
    """State for managing interactions"""
    thread_id: Optional[str] = None
    participants: List[str] = Field(default_factory=list)
    topics: List[str] = Field(default_factory=list)
    sentiment: float = 0.0
    intensity: float = 0.5
    timestamp: datetime = Field(default_factory=datetime.now)

class ResponseState(BaseModel):
    """State for managing responses"""
    response_type: Optional[str] = None
    response_content: Optional[str] = None
    queued_responses: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.now)

class GonzoState(BaseModel):
    """Root state class for Gonzo"""
    messages: MessageState = Field(default_factory=MessageState)
    analysis: AnalysisState = Field(default_factory=AnalysisState)
    evolution: EvolutionState = Field(default_factory=EvolutionState)
    interaction: InteractionState = Field(default_factory=InteractionState)
    response: ResponseState = Field(default_factory=ResponseState)
    memory: MemoryState = Field(default_factory=MemoryState)
    x_state: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    
    def calculate_pattern_significance(self) -> float:
        """Calculate significance based on patterns, giving higher weight to manipulation patterns"""
        if not self.analysis.patterns:
            return 0.0
            
        base_significance = len(self.analysis.patterns) * 0.2
        manipulation_multiplier = 1.5 if any(
            'manipulation' in str(p.get('content', '')).lower() or 
            p.get('type') == 'manipulation' 
            for p in self.analysis.patterns
        ) else 1.0
        
        return min(1.0, base_significance * manipulation_multiplier)
    
    def update_analysis(self) -> None:
        """Update analysis state based on current patterns"""
        self.analysis.significance = self.calculate_pattern_significance()
        self.analysis.timestamp = datetime.now()
        
    def get_from_memory(self, key: str, memory_type: str = "short_term") -> Any:
        """Get value from memory.
        
        Args:
            key: Memory key
            memory_type: Either 'short_term' or 'long_term'
        """
        memory = getattr(self.memory, memory_type, {})
        return memory.get(key)
        
    def save_to_memory(self, key: str, value: Any, memory_type: str = "short_term", permanent: bool = False) -> None:
        """Save value to memory.
        
        Args:
            key: Memory key
            value: Value to store
            memory_type: Either 'short_term' or 'long_term'
            permanent: Whether to make the memory permanent
        """
        memory = getattr(self.memory, memory_type, {})
        memory[key] = value
        setattr(self.memory, memory_type, memory)
        
    def add_error(self, error: str) -> None:
        """Add error message to memory.
        
        Args:
            error: Error message
        """
        self.memory.errors.append(f"{datetime.now().isoformat()}: {error}")

def create_initial_state() -> GonzoState:
    """Create the initial state for Gonzo"""
    return GonzoState()