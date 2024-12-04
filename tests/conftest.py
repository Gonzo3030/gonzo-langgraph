import pytest

# Configure all tests to use asyncio by default
pytest_plugins = ['pytest_asyncio']

@pytest.fixture(scope='session')
def event_loop():
    """Create an instance of the default event loop for each test case."""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()