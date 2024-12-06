import pytest
from time import time
from gonzo.recovery import ErrorHandler, RetryHandler, ExponentialBackoff, LinearBackoff

@pytest.fixture
def error_handler():
    """Create test error handler."""
    return ErrorHandler()

@pytest.fixture
def retry_handler():
    """Create test retry handler."""
    return RetryHandler(max_retries=3)

def test_basic_error_handling(error_handler):
    """Test basic error handling."""
    # Create test error
    try:
        raise ValueError("Test error")
    except Exception as e:
        error_handler.handle(e, {"step": 1})
    
    # Check error recording
    errors = error_handler.get_errors()
    assert len(errors) == 1
    assert errors[0]["type"] == "ValueError"
    
    # Test clearing errors
    error_handler.clear_errors()
    assert len(error_handler.get_errors()) == 0

@pytest.mark.asyncio
async def test_retry_handling(retry_handler):
    """Test retry handling logic."""
    context = {"step": 1, "node": "test"}
    
    # Test retryable error
    error = ValueError("Test error")
    assert retry_handler.should_retry(error, context)
    
    # Test non-retryable error
    error = KeyError("Test error")
    assert not retry_handler.should_retry(error, context)
    
    # Test max retries
    error = ValueError("Test error")
    for _ in range(4):  # More than max_retries
        if not retry_handler.should_retry(error, context):
            break
    assert not retry_handler.should_retry(error, context)

def test_exponential_backoff():
    """Test exponential backoff policy."""
    policy = ExponentialBackoff(base_delay=1.0)
    
    delays = [
        policy.get_delay(retry)
        for retry in range(4)
    ]
    
    # Check exponential growth
    assert all(delays[i] < delays[i+1] for i in range(len(delays)-1))
    assert delays[0] == 1.0  # Base delay
    assert delays[1] == 2.0  # First backoff

def test_linear_backoff():
    """Test linear backoff policy."""
    policy = LinearBackoff(base_delay=1.0, increment=2.0)
    
    delays = [
        policy.get_delay(retry)
        for retry in range(4)
    ]
    
    # Check linear growth
    assert all(delays[i+1] - delays[i] == 2.0 for i in range(len(delays)-1))
    assert delays[0] == 1.0  # Base delay
    assert delays[1] == 3.0  # First backoff