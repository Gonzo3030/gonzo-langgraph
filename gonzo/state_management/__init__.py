"""State management for Gonzo system."""
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel

class WorkflowStage(str, Enum):
    """Workflow stages for Gonzo's operation"""
    INITIALIZATION = "initialization"
    MARKET_MONITORING = "market_monitoring"
    SOCIAL_MONITORING = "social_monitoring"
    NEWS_MONITORING = "news_monitoring"
    PATTERN_ANALYSIS = "pattern_analysis"
    NARRATIVE_GENERATION = "narrative_generation"
    RESPONSE_POSTING = "response_posting"
    ERROR_RECOVERY = "error_recovery"
    CYCLE_COMPLETE = "cycle_complete"
    SHUTDOWN = "shutdown"

class APICredentials(BaseModel):
    """API credentials model"""
    api_key: str = ""
    api_secret: str = ""
    access_token: str = ""
    access_secret: str = ""

class MarketData(BaseModel):
    """Market data structure"""
    price: float
    timestamp: datetime
    volume: float
    change_24h: float
    symbol: str

class SocialData(BaseModel):
    """Social media data structure"""
    content: str
    timestamp: datetime
    metrics: Dict[str, int]
    author_id: str

class NewsData(BaseModel):
    """News data structure"""
    title: str
    url: str
    published_date: datetime
    source: str
    description: str
    relevance_score: float
    topics: List[str]
    sentiment: float
    related_assets: List[str] = []

class Analysis(BaseModel):
    """Analysis results structure"""
    market_patterns: List[Dict[str, Any]] = []
    social_patterns: List[Dict[str, Any]] = []
    news_patterns: List[Dict[str, Any]] = []
    correlations: List[Dict[str, Any]] = []
    sentiment_score: float = 0.0
    significance: float = 0.0
    generated_narrative: Optional[str] = None

class NarrativeContext(BaseModel):
    """Narrative context structure"""
    market_events: List[Dict[str, Any]] = []
    social_events: List[Dict[str, Any]] = []
    news_events: List[Dict[str, Any]] = []
    patterns: List[Dict[str, Any]] = []
    topics: List[str] = []
    pending_analyses: bool = False

class XIntegration(BaseModel):
    """X Integration state"""
    direct_api: Dict[str, str] = {}
    queued_posts: List[Dict[str, Any]] = []
    rate_limits: Dict[str, Any] = {
        "remaining": 180,
        "reset_time": None,
        "last_request": None
    }

class Memory(BaseModel):
    """Memory system"""
    short_term: Dict[str, Any] = {}
    long_term: Dict[str, Any] = {}
    
    def store(self, key: str, value: Any, memory_type: str = "short_term"):
        """Store data in memory"""
        if memory_type == "long_term":
            self.long_term[key] = value
        else:
            self.short_term[key] = value

class UnifiedState(BaseModel):
    """Complete unified state for Gonzo"""
    # Workflow control
    current_stage: WorkflowStage = WorkflowStage.INITIALIZATION
    
    # Message handling
    messages: List[str] = []
    api_queries: List[str] = []
    api_responses: Dict[str, Any] = {}
    api_errors: List[str] = []
    next_steps: List[str] = []
    
    # Core components
    market_data: Dict[str, MarketData] = {}
    social_data: List[SocialData] = []
    news_data: List[NewsData] = []
    analysis: Analysis = Analysis()
    narrative: NarrativeContext = NarrativeContext()
    
    # Integration states
    x_integration: XIntegration = XIntegration()
    
    # Memory system
    memory: Memory = Memory()
    
    def add_message(self, content: str, source: str = "system"):
        """Add a message with metadata"""
        timestamp = datetime.utcnow().isoformat()
        message = f"[{timestamp}] [{source}] {content}"
        self.messages.append(message)

def create_initial_state() -> UnifiedState:
    """Create the initial state for Gonzo"""
    return UnifiedState()