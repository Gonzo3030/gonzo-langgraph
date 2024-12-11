import pytest
from datetime import datetime
from pydantic import BaseModel
from typing import List, Dict, Optional

# Test-specific state models
class TestMonitoringState(BaseModel):
    tracked_topics: List[str] = []
    tracked_users: List[str] = []
    last_check_times: Dict[str, datetime] = {}
    current_trends: List[str] = []
    last_trends_update: Optional[datetime] = None
    error_log: List[Dict] = []

    def log_error(self, message: str, context: dict = None):
        self.error_log.append({
            'timestamp': datetime.now(),
            'message': message,
            'context': context or {}
        })

@pytest.fixture
def mock_state():
    """Create a mock state for testing."""
    return TestMonitoringState(
        tracked_topics=["bitcoin", "ai"],
        tracked_users=["resistance_user"],
        current_trends=["crypto", "tech"],
        last_trends_update=datetime.now()
    )