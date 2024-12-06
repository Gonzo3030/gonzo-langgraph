import pytest
from gonzo.types import create_initial_state
from gonzo.graph.workflow import create_workflow
from langchain_core.messages import HumanMessage

@pytest.fixture
def workflow():
    """Create test workflow instance."""
    return create_workflow()

@pytest.fixture
def initial_state():
    """Create test initial state."""
    return create_initial_state(
        HumanMessage(content="What's happening with Bitcoin today?")
    )