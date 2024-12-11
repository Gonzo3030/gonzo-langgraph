from typing import Dict
from pydantic import BaseModel
from datetime import timedelta

class XConfig(BaseModel):
    """Configuration for X integration."""
    # Rate limits (requests per window)
    rate_limits: Dict[str, Dict[str, int]] = {
        'post': {'requests': 200, 'window': 3600},  # 200 per hour
        'read': {'requests': 180, 'window': 900},   # 180 per 15 min
        'search': {'requests': 180, 'window': 900},  # 180 per 15 min
    }
    
    # Monitoring intervals
    monitoring_intervals: Dict[str, int] = {
        'mentions': 60,      # Check mentions every 60 seconds
        'metrics': 300,      # Update metrics every 5 minutes
        'topics': 300,       # Check topics every 5 minutes
    }
    
    # Queue settings
    queue_settings: Dict[str, Any] = {
        'max_queue_size': 100,
        'default_priority': 1,
        'max_retry_attempts': 3,
        'retry_delay': timedelta(minutes=5),
    }
    
    # Content filters
    content_filters: Dict[str, Any] = {
        'max_content_length': 280,
        'required_hashtags': [],
        'blocked_keywords': [],
    }

# Default configuration
default_config = XConfig()

def get_x_config() -> XConfig:
    """Get X configuration, allowing for environment overrides."""
    return default_config  # TODO: Add environment override support