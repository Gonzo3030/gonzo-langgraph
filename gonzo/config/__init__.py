# Config package initialization
from .topics import TopicConfiguration

# Model Configuration
MODEL_NAME = "claude-3-opus-20240229"  # Default model
MODEL_TEMPERATURE = 0.7

# System Configuration
MAX_RETRIES = 3
BASE_DELAY = 1  # Base delay for exponential backoff

__all__ = [
    'TopicConfiguration',
    'MODEL_NAME',
    'MODEL_TEMPERATURE',
    'MAX_RETRIES',
    'BASE_DELAY'
]