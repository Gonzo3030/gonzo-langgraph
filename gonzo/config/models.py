"""Model configuration for Gonzo's LLM interface."""

from typing import Dict, Any

# Core model configuration
MODEL_CONFIG = {
    "model": "claude-3-sonnet-20241022",
    "max_tokens": 4096,
    "temperature": 0.7,
    "top_p": 1.0
}

# Model name constant
MODEL_NAME = MODEL_CONFIG["model"]

# Runtime configuration for graph
GRAPH_CONFIG = {
    "configurable": {
        "model": MODEL_NAME,
        "streaming": True
    }
}