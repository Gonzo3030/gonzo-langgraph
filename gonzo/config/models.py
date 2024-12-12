"""Model configurations for language models."""

# Core models
MODEL_NAME = "claude-3.5-sonnet"  # Default model
ANTHROPIC_MODEL = "claude-3.5-sonnet"  # Latest Claude 3.5 Sonnet version
GPT4_MODEL = "gpt-4-turbo-preview"

# Model configurations
MODEL_CONFIGS = {
    "claude-3.5-sonnet": {
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