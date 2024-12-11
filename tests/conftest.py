import pytest
from datetime import datetime
from pydantic import BaseModel
from typing import List, Dict, Optional
from unittest.mock import patch
from .mocks.llm import MockChatOpenAI
from gonzo.utils.llm import set_llm

# Test-specific base models to avoid deep imports
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

class TestXState(BaseModel):
    monitoring: TestMonitoringState = TestMonitoringState()
    last_monitor_time: Optional[datetime] = None

@pytest.fixture(autouse=True)
def mock_llm():
    """Set up mock LLM for all tests."""
    mock_llm = MockChatOpenAI()
    set_llm(mock_llm)
    return mock_llm

@pytest.fixture
def mock_state():
    """Create a mock state for testing."""
    return TestXState(
        monitoring=TestMonitoringState(
            tracked_topics=["bitcoin", "ai"],
            tracked_users=["resistance_user"],
            current_trends=["crypto", "tech"],
            last_trends_update=datetime.now()
        )
    )

@pytest.fixture
def mock_client():
    """Create a mock client for testing."""
    class MockClient:
        async def fetch_mentions(self, *args, **kwargs):
            return []
        
        async def search_recent(self, *args, **kwargs):
            return []
        
        async def fetch_metrics(self, *args, **kwargs):
            return {}
    
    return MockClient()