from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from datetime import datetime

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

class Analysis(BaseModel):
    """Analysis results structure"""
    market_patterns: List[Dict[str, Any]] = []
    social_patterns: List[Dict[str, Any]] = []
    correlations: List[Dict[str, Any]] = []
    sentiment_score: float = 0.0
    significance: float = 0.0
    generated_narrative: Optional[str] = None

class NarrativeContext(BaseModel):
    """Narrative context structure"""
    market_events: List[Dict[str, Any]] = []
    social_events: List[Dict[str, Any]] = []
    patterns: List[Dict[str, Any]] = []
    topics: List[str] = []
    pending_analyses: bool = False

class XIntegration(BaseModel):
    """X Integration state"""
    direct_api: Optional[APICredentials] = None
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
    messages: List[str] = []
    api_queries: List[str] = []
    api_responses: Dict[str, Any] = {}
    api_errors: List[str] = []
    next_steps: List[str] = []
    
    # Core components
    market_data: Dict[str, MarketData] = {}
    social_data: List[SocialData] = []
    analysis: Analysis = Analysis()
    narrative: NarrativeContext = NarrativeContext()
    
    # Integration states
    x_integration: XIntegration = XIntegration()
    
    # Memory system
    memory: Memory = Memory()

def create_initial_state() -> UnifiedState:
    """Create the initial state for Gonzo"""
    return UnifiedState()

def update_rate_limits(state: UnifiedState, remaining: int, reset_time: datetime) -> UnifiedState:
    """Update X API rate limiting information"""
    state.x_integration.rate_limits.update({
        "remaining": remaining,
        "reset_time": reset_time,
        "last_request": datetime.now()
    })
    return state

def should_throttle(state: UnifiedState) -> bool:
    """Check if we should throttle X API requests"""
    limits = state.x_integration.rate_limits
    if limits["remaining"] <= 1:  # Keep 1 request in reserve
        if limits["reset_time"] and datetime.now() < limits["reset_time"]:
            return True
    return False