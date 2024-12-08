from typing import TypedDict, Optional, Dict, Any, List
from datetime import datetime

class APIState:
    """Manages the state of API interactions."""
    def __init__(self):
        self.request_history: List[Dict[str, Any]] = []
        self.rate_limits: Dict[str, int] = {}
        self.errors: List[Dict[str, Any]] = []
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary for serialization."""
        return {
            "request_history": self.request_history,
            "rate_limits": self.rate_limits,
            "errors": self.errors
        }

class APIRequestState(TypedDict):
    endpoint: str
    timestamp: datetime
    parameters: Dict[str, Any]
    status: str  # 'pending', 'completed', 'failed'

class APIResponseState(TypedDict):
    request_id: str
    data: Optional[Dict[str, Any]]
    error: Optional[str]
    timestamp: datetime

class APIStateManager:
    def __init__(self):
        self.requests: Dict[str, APIRequestState] = {}
        self.responses: Dict[str, APIResponseState] = {}
        self.active_endpoints: List[str] = []
    
    def register_request(self, endpoint: str, parameters: Dict[str, Any]) -> str:
        """Register a new API request and return its ID."""
        request_id = f"{endpoint}_{datetime.now().timestamp()}"
        self.requests[request_id] = {
            "endpoint": endpoint,
            "timestamp": datetime.now(),
            "parameters": parameters,
            "status": "pending"
        }
        return request_id
    
    def update_request_status(self, request_id: str, status: str):
        """Update the status of an existing request."""
        if request_id in self.requests:
            self.requests[request_id]["status"] = status
    
    def store_response(self, request_id: str, data: Optional[Dict[str, Any]] = None, error: Optional[str] = None):
        """Store an API response or error."""
        self.responses[request_id] = {
            "request_id": request_id,
            "data": data,
            "error": error,
            "timestamp": datetime.now()
        }