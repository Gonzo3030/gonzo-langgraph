from datetime import datetime
from typing import Dict, List, Optional, Any, Literal
from uuid import UUID, uuid4
from enum import Enum
from pydantic import BaseModel, Field, model_validator

class KnowledgeGraphState(BaseModel):
    """State for knowledge graph components"""
    entities: Dict[str, Any] = Field(default_factory=dict)
    relationships: Dict[str, Any] = Field(default_factory=dict)
    patterns: List[Dict[str, Any]] = Field(default_factory=list)
    sentiment_scores: Dict[str, float] = Field(default_factory=dict)
    themes: List[str] = Field(default_factory=list)
    last_updated: datetime = Field(default_factory=datetime.utcnow)

class AssessmentState(BaseModel):
    """State for assessment flow"""
    content_analysis: Dict[str, Any] = Field(default_factory=dict)
    entity_extraction: List[Dict[str, Any]] = Field(default_factory=list)
    sentiment_analysis: Dict[str, float] = Field(default_factory=dict)
    confidence_scores: Dict[str, float] = Field(default_factory=dict)

class NarrativeState(BaseModel):
    """State for narrative flow"""
    context: Dict[str, Any] = Field(default_factory=dict)
    story_elements: List[Dict[str, Any]] = Field(default_factory=list)
    themes: List[str] = Field(default_factory=list)
    style_parameters: Dict[str, Any] = Field(default_factory=dict)

class EvolutionState(BaseModel):
    """State for evolution system"""
    adaptation_metrics: Dict[str, float] = Field(default_factory=dict)
    learning_history: List[Dict[str, Any]] = Field(default_factory=list)
    behavior_modifiers: Dict[str, Any] = Field(default_factory=dict)
    last_evolution: datetime = Field(default_factory=datetime.utcnow)

class XIntegrationState(BaseModel):
    """State for X integration"""
    direct_api: Dict[str, Any] = Field(default_factory=dict)
    openapi_state: Dict[str, Any] = Field(default_factory=dict)
    rate_limits: Dict[str, datetime] = Field(default_factory=dict)
    queued_posts: List[Dict[str, Any]] = Field(default_factory=list)
    interaction_queue: List[Dict[str, Any]] = Field(default_factory=list)
    post_history: List[Dict[str, Any]] = Field(default_factory=list)

class MemoryState(BaseModel):
    """Enhanced memory system state"""
    short_term: Dict[str, Any] = Field(default_factory=dict)
    long_term: Dict[str, Any] = Field(default_factory=dict)
    episodic: List[Dict[str, Any]] = Field(default_factory=list)
    semantic: Dict[str, Any] = Field(default_factory=dict)
    procedural: Dict[str, List[str]] = Field(default_factory=dict)
    last_accessed: Dict[str, datetime] = Field(default_factory=dict)

class WorkflowStage(str, Enum):
    """Enhanced workflow stages"""
    MONITOR = "monitor"
    RAG_ANALYSIS = "rag_analysis"
    PATTERN_DETECT = "pattern_detect"
    ASSESS = "assess"
    NARRATE = "narrate"
    RESPOND = "respond"
    QUEUE = "queue"
    POST = "post"
    INTERACT = "interact"
    EVOLVE = "evolve"
    ERROR = "error"
    END = "end"

class UnifiedState(BaseModel):
    """Unified state management for Gonzo"""
    # Core identification
    session_id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Workflow control
    current_stage: WorkflowStage = Field(default=WorkflowStage.MONITOR)
    next_stage: Optional[WorkflowStage] = None
    checkpoint_needed: bool = False
    
    # Core components state
    knowledge_graph: KnowledgeGraphState = Field(default_factory=KnowledgeGraphState)
    assessment: AssessmentState = Field(default_factory=AssessmentState)
    narrative: NarrativeState = Field(default_factory=NarrativeState)
    evolution: EvolutionState = Field(default_factory=EvolutionState)
    
    # Integration state
    x_integration: XIntegrationState = Field(default_factory=XIntegrationState)
    
    # Memory and context
    memory: MemoryState = Field(default_factory=MemoryState)
    current_context: Dict[str, Any] = Field(default_factory=dict)
    
    # Error handling
    errors: List[str] = Field(default_factory=list)
    last_error: Optional[str] = None

    def create_checkpoint(self) -> Dict[str, Any]:
        """Create comprehensive checkpoint"""
        return self.model_dump()
    
    @classmethod
    def restore_from_checkpoint(cls, checkpoint: Dict[str, Any]) -> 'UnifiedState':
        """Restore complete state from checkpoint"""
        return cls(**checkpoint)
    
    def transition_to(self, next_stage: WorkflowStage) -> None:
        """Handle stage transition with state validation"""
        self.checkpoint_needed = True
        self.current_stage = next_stage
        self.timestamp = datetime.utcnow()
    
    def record_error(self, error: str, critical: bool = False) -> None:
        """Enhanced error recording"""
        self.errors.append({
            "error": error,
            "timestamp": datetime.utcnow(),
            "stage": self.current_stage,
            "critical": critical
        })
        self.last_error = error
        if critical:
            self.transition_to(WorkflowStage.ERROR)

def create_initial_state() -> UnifiedState:
    """Create new initial state"""
    return UnifiedState()

def update_state(current_state: UnifiedState, updates: Dict[str, Any]) -> UnifiedState:
    """Update state while maintaining immutability"""
    state_dict = current_state.model_dump()
    for key, value in updates.items():
        if key in state_dict:
            state_dict[key] = value
    return UnifiedState(**state_dict)
