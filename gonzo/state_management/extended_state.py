from datetime import datetime
from typing import Dict, List, Optional, Any, Literal
from uuid import UUID, uuid4
from enum import Enum
from pydantic import BaseModel, Field, model_validator

class StateType(str, Enum):
    """Types of state data"""
    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"
    PERSISTENT = "persistent"

class WorkflowStage(str, Enum):
    """Stages in the Gonzo workflow"""
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

class Memory(BaseModel):
    """Memory storage with temporal awareness"""
    short_term: Dict[str, Any] = Field(default_factory=dict)
    long_term: Dict[str, Any] = Field(default_factory=dict)
    last_accessed: Dict[str, datetime] = Field(default_factory=dict)
    
    def store(self, key: str, value: Any, memory_type: StateType) -> None:
        """Store a value in memory with timestamp"""
        target = self.short_term if memory_type == StateType.SHORT_TERM else self.long_term
        target[key] = value
        self.last_accessed[key] = datetime.utcnow()
    
    def retrieve(self, key: str, memory_type: StateType) -> Optional[Any]:
        """Retrieve a value from memory"""
        target = self.short_term if memory_type == StateType.SHORT_TERM else self.long_term
        if key in target:
            self.last_accessed[key] = datetime.utcnow()
            return target[key]
        return None

class RAGContext(BaseModel):
    """Context from RAG system"""
    query: Optional[str] = None
    retrieved_documents: List[Dict[str, Any]] = Field(default_factory=list)
    relevance_scores: Dict[str, float] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class Message(BaseModel):
    """Message with metadata"""
    id: UUID = Field(default_factory=uuid4)
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    source: Optional[str] = None

class XIntegrationState(BaseModel):
    """State for X integration"""
    queued_posts: List[str] = Field(default_factory=list)
    posted_ids: List[str] = Field(default_factory=list)
    last_post_time: Optional[datetime] = None
    rate_limit_reset: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

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
    memory: Memory = Field(default_factory=Memory)
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
