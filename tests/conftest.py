import pytest
from gonzo.state.x_state import XState, MonitoringState
from datetime import datetime

@pytest.fixture
def mock_base_state():
    """Create a mock base state for testing."""
    return XState(
        monitoring=MonitoringState(
            tracked_topics=["bitcoin", "ai"],
            tracked_users=["resistance_user"],
            last_check_times={},
            current_trends=["crypto", "tech"],
            last_trends_update=datetime.now()
        )
    )