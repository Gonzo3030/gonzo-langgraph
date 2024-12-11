# Core configuration
from .topics import TopicConfiguration

# Model Configuration
MODEL_NAME = "claude-3-opus-20240229"

# API Configuration
def get_api_keys():
    """Get API keys from environment.
    In production, this would load from environment variables or secure storage.
    For testing, we can return mock keys.
    """
    return {
        "api_key": "test_key",
        "api_secret": "test_secret",
        "access_token": "test_token",
        "access_secret": "test_secret"
    }

__all__ = ['TopicConfiguration', 'MODEL_NAME', 'get_api_keys']