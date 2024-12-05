import pytest
from datetime import datetime
from gonzo.state_management.api_state import APIStateManager

@pytest.fixture
def api_state_manager():
    return APIStateManager()

def test_register_request(api_state_manager):
    endpoint = "crypto/prices"
    params = {"symbol": "BTC"}
    
    request_id = api_state_manager.register_request(endpoint, params)
    
    assert request_id in api_state_manager.requests
    assert api_state_manager.requests[request_id]["endpoint"] == endpoint
    assert api_state_manager.requests[request_id]["parameters"] == params
    assert api_state_manager.requests[request_id]["status"] == "pending"

def test_update_request_status(api_state_manager):
    endpoint = "crypto/prices"
    params = {"symbol": "BTC"}
    request_id = api_state_manager.register_request(endpoint, params)
    
    api_state_manager.update_request_status(request_id, "completed")
    
    assert api_state_manager.requests[request_id]["status"] == "completed"

def test_store_response(api_state_manager):
    endpoint = "crypto/prices"
    params = {"symbol": "BTC"}
    request_id = api_state_manager.register_request(endpoint, params)
    
    response_data = {"price": 50000}
    api_state_manager.store_response(request_id, data=response_data)
    
    assert request_id in api_state_manager.responses
    assert api_state_manager.responses[request_id]["data"] == response_data
    assert api_state_manager.responses[request_id]["error"] is None