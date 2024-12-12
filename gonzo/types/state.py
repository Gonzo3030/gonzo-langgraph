from typing import Dict, List, Optional, Any, Set
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum

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

class GonzoState(BaseModel):
    """Complete state for Gonzo agent"""
    # Input state
    input_text: Optional[str] = None
    input_type: Optional[str] = None
    source_id: Optional[str] = None
    
    # Analysis state
    patterns: List[Dict[str, Any]] = Field(default_factory=list)
    entities: List[Dict[str, Any]] = Field(default_factory=list)
    historical_connections: Dict[str, float] = Field(default_factory=dict)
    current_significance: float = 0.5
    
    # Evolution state
    evolution: EvolutionState = Field(default_factory=lambda: EvolutionState(timestamp=datetime.now()))
    
    # Interaction state
    interaction: InteractionState = Field(default_factory=lambda: InteractionState(timestamp=datetime.now()))
    
    # Response state
    response_type: Optional[str] = None
    response_content: Optional[str] = None
    response_sent: bool = False
    
    # Memory state
    processed_ids: Set[str] = Field(default_factory=set)
    memory_references: List[str] = Field(default_factory=list)
    
    def update_with_analysis(self, analysis_results: Dict[str, Any]):
        """Update state with new analysis results"""
        if 'patterns' in analysis_results:
            self.patterns.extend(analysis_results['patterns'])
        if 'entities' in analysis_results:
            self.entities.extend(analysis_results['entities'])
        if 'historical_connections' in analysis_results:
            self.historical_connections.update(analysis_results['historical_connections'])
        if 'significance' in analysis_results:
            self.current_significance = analysis_results['significance']
            
    class Config:
        arbitrary_types_allowed = True