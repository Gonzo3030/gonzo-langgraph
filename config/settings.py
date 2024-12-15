"""Core configuration settings for the Gonzo LangGraph system."""

import os
import yaml
from typing import Dict, Any

DEFAULT_CONFIG = {
    'response': {
        'frequency': {
            'min_interval': 300,  # 5 minutes
            'max_per_hour': 30
        },
        'content': {
            'min_length': 50,
            'max_length': 280,
            'require_approval': False
        }
    },
    'evolution': {
        'memory_retention': 7200,  # 2 hours
        'learning_rate': 0.1,
        'adaptation_threshold': 0.75
    },
    'monitoring': {
        'health_check_interval': 300,  # 5 minutes
        'log_level': 'INFO',
        'metrics_enabled': True
    },
    'rate_limits': {
        'x': {
            'tweets_per_hour': 25,
            'mentions_per_minute': 5
        },
        'youtube': {
            'requests_per_day': 10000
        },
        'openai': {
            'requests_per_minute': 60
        }
    },
    'content_filters': {
        'blocked_terms': [],
        'sensitive_topics': [],
        'max_toxicity_score': 0.7
    }
}

def load_config() -> Dict[str, Any]:
    """Load configuration from file or use defaults"""
    config_path = os.getenv('GONZO_CONFIG', 'config/config.yml')
    
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                user_config = yaml.safe_load(f)
                # Deep merge user config with defaults
                return deep_merge(DEFAULT_CONFIG, user_config)
    except Exception as e:
        print(f'Warning: Failed to load config file: {str(e)}')
    
    return DEFAULT_CONFIG

def deep_merge(default: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two dictionaries"""
    result = default.copy()
    
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    
    return result
