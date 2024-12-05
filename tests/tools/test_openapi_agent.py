import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from gonzo.tools.openapi_agent import OpenAPIAgentTool, APIState

@pytest.fixture
def mock_llm():
    return MagicMock()

@pytest.fixture
def api_agent(mock_llm):
    return OpenAPIAgentTool(llm=mock_llm)

def test_api_state_initialization(api_agent):
    assert isinstance(api_agent.state, APIState)
    assert api_agent.state.last_request_time is None
    assert isinstance(api_agent.state.rate_limits, dict)
    assert isinstance(api_agent.state.cached_responses, dict)
    assert isinstance(api_agent.state.active_connections, list)

@patch('builtins.open')
@patch('langchain.agents.create_openapi_agent')
@patch('langchain.agents.agent_toolkits.OpenAPIToolkit.from_llm')
def test_create_agent_for_api(mock_toolkit, mock_create_agent, mock_open, api_agent):
    mock_agent = MagicMock()
    mock_create_agent.return_value = mock_agent
    
    result = api_agent.create_agent_for_api('dummy_path.yaml', 'test_api')
    
    assert result is True
    assert 'test_api' in api_agent.active_agents
    assert 'test_api' in api_agent.state.active_connections

def test_rate_limit_handling(api_agent):
    api_agent.add_rate_limit('test_api', 60)  # 60 second rate limit
    api_agent.state.last_request_time = datetime.now()
    
    with pytest.raises(ValueError, match='Rate limit exceeded'):
        api_agent.query_api('test_api', 'test query')

def test_cache_handling(api_agent):
    # Setup mock response
    mock_response = {'data': 'test_data'}
    cache_key = 'test_api:test query'
    api_agent.state.cached_responses[cache_key] = {
        'data': mock_response,
        'timestamp': datetime.now()
    }
    
    # Test cache hit
    result = api_agent.query_api('test_api', 'test query')
    assert result == mock_response

def test_cache_expiration(api_agent):
    # Setup expired cache
    mock_response = {'data': 'test_data'}
    cache_key = 'test_api:test query'
    api_agent.state.cached_responses[cache_key] = {
        'data': mock_response,
        'timestamp': datetime.now() - timedelta(seconds=301)  # Expired
    }
    
    # Mock agent response for expired cache
    mock_agent = MagicMock()
    mock_agent.run.return_value = {'data': 'new_data'}
    api_agent.active_agents['test_api'] = mock_agent
    
    result = api_agent.query_api('test_api', 'test query')
    assert result == {'data': 'new_data'}

def test_clear_cache(api_agent):
    # Setup cache
    api_agent.state.cached_responses = {
        'api1:query1': {'data': 'data1', 'timestamp': datetime.now()},
        'api2:query1': {'data': 'data2', 'timestamp': datetime.now()}
    }
    
    # Test clearing specific API cache
    api_agent.clear_cache('api1')
    assert 'api1:query1' not in api_agent.state.cached_responses
    assert 'api2:query1' in api_agent.state.cached_responses
    
    # Test clearing all cache
    api_agent.clear_cache()
    assert len(api_agent.state.cached_responses) == 0