import pytest
from gonzo.nodes.api_node import APINode
from gonzo.state import GonzoState

@pytest.fixture
def api_node():
    return APINode()

@pytest.fixture
def mock_state():
    return GonzoState()

def test_api_node_initialization(api_node):
    assert hasattr(api_node, 'tool_executor')
    assert len(api_node.tool_executor.tools) == 0

def test_add_api_tool(api_node):
    def dummy_func():
        return 'test'
    
    api_node.add_api_tool('test_tool', dummy_func, 'Test description')
    assert len(api_node.tool_executor.tools) == 1
    assert api_node.tool_executor.tools[0].name == 'test_tool'