"""State management for Gonzo LangGraph system."""

from typing import Dict, List, Optional, Any, Set
from datetime import datetime
from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage

class BaseGonzoState(BaseModel):
    """Base state class for all Gonzo states"""
    timestamp: datetime = Field(default_factory=datetime.now)

class MessageState(BaseGonzoState):
    """State for message handling"""
    messages: List[BaseMessage] = Field(default_factory=list)
    current_message: Optional[str] = None

class AnalysisState(BaseGonzoState):
    """State for content analysis"""
    patterns: List[Dict[str, Any]] = Field(default_factory=list)
    entities: List[Dict[str, Any]] = Field(default_factory=list)
    significance: float = 0.5
    temporal_connections: Dict[str, float] = Field(default_factory=dict)

class EvolutionState(BaseGonzoState):
    """State for evolution tracking"""
    pattern_confidence: float = 0.5
    narrative_consistency: float = 0.5
    prediction_accuracy: float = 0.5
    processed_content_ids: List[str] = Field(default_factory=list)

class ResponseState(BaseGonzoState):
    """State for response generation"""
    response_type: Optional[str] = None
    response_content: Optional[str] = None
    queued_responses: List[Dict[str, Any]] = Field(default_factory=list)

class GonzoState(BaseGonzoState):
    """Complete state for Gonzo agent"""
    messages: MessageState = Field(default_factory=MessageState)
    analysis: AnalysisState = Field(default_factory=AnalysisState)
    evolution: EvolutionState = Field(default_factory=EvolutionState)
    response: ResponseState = Field(default_factory=ResponseState)
    
    class Config:
        arbitrary_types_allowed = True

def create_initial_state(
    messages: Optional[List[BaseMessage]] = None,
    **kwargs
) -> GonzoState:
    """Create initial state for workflow.
    
    Args:
        messages: Optional initial messages
        **kwargs: Additional state parameters
        
    Returns:
        Initialized GonzoState
    """
    state = GonzoState(
        messages=MessageState(messages=messages or []),
        **kwargs
    )
    return state