"""Model configurations for language models."""

# Core models
MODEL_NAME = "claude-3-sonnet-20240229"  # Default model
ANTHROPIC_MODEL = "claude-3-sonnet-20240229"
GPT4_MODEL = "gpt-4-turbo-preview"

# Model configurations
MODEL_CONFIGS = {
    "claude-3-sonnet-20240229": {
        "max_tokens": 4096,
        "temperature": 0.7,
        "top_p": 1.0
    },
    "gpt-4-turbo-preview": {
        "max_tokens": 4096,
        "temperature": 0.7,
        "top_p": 1.0
    }
}