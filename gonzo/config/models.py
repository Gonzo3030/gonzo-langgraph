"""Model configurations for Gonzo system."""

# Claude configuration
ANTHROPIC_MODEL = "claude-3-opus-20240229"
OPENAI_MODEL = "gpt-4-turbo-preview"

MODEL_NAME = ANTHROPIC_MODEL

MODEL_CONFIG = {
    "temperature": 0.7,
    "max_tokens": 1000,
    "presence_penalty": 0.0,
    "frequency_penalty": 0.0
}

GRAPH_CONFIG = {
    "max_iterations": 5,
    "max_time": 30,  # seconds
    "early_stopping": True
}