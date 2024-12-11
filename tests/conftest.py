import pytest
from gonzo.types.base import create_initial_state
from gonzo.graph.workflow import create_workflow
from gonzo.state.x_state import XState, MonitoringState
from gonzo.types.social import QueuedPost
from langchain_core.messages import HumanMessage

@pytest.fixture
def workflow():
    """Create test workflow instance."""
    return create_workflow()

@pytest.fixture
def initial_state():
    """Create test initial state."""
    state = create_initial_state()
    state.messages.append(HumanMessage(content="What's happening with Bitcoin today?"))
    return state

@pytest.fixture
def x_state():
    """Create test X state."""
    return XState()

@pytest.fixture
def monitoring_state():
    """Create test monitoring state."""
    return MonitoringState()

@pytest.fixture
def queued_post():
    """Create test queued post."""
    return QueuedPost(
        content="Test post from Gonzo",
        priority=1
    )