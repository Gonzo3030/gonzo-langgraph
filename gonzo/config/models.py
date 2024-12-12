"""Model configurations for language models."""

# Core models
MODEL_NAME = "claude-3-sonnet-20241022"  # Default model - Latest Claude 3.5 Sonnet

# Model configurations
MODEL_CONFIGS = {
    "claude-3-sonnet-20241022": {
        "max_tokens": 4096,
        "temperature": 0.7,
        "top_p": 1.0
    }
}