import os
from dotenv import load_dotenv
from typing import Dict

# Load environment variables
load_dotenv()

# Model Configuration
MODEL_NAME = "gpt-4-1106-preview"

# LangSmith Configuration
LANGCHAIN_TRACING_V2 = True
LANGCHAIN_PROJECT = "gonzo-langgraph"
LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY")

# OpenAI Configuration (for analysis tasks)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = MODEL_NAME

# Anthropic Configuration (for response generation)
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ANTHROPIC_MODEL = "claude-3-sonnet-20240229"  # Latest Claude 3.5 Sonnet

# X API Configuration
X_API_KEY = os.getenv("X_API_KEY")
X_API_SECRET = os.getenv("X_API_SECRET")
X_ACCESS_TOKEN = os.getenv("X_ACCESS_TOKEN")
X_ACCESS_SECRET = os.getenv("X_ACCESS_SECRET")  # Changed to match .env
X_BEARER_TOKEN = os.getenv("X_BEARER_TOKEN")

# X API Rate Limiting Configuration
X_MAX_RETRIES = 3
X_BASE_DELAY = 5  # Base delay in seconds for exponential backoff
X_MAX_DELAY = 300  # Maximum delay in seconds

# Brave Search Configuration
BRAVE_API_KEY = os.getenv("BRAVE_API_KEY")

def get_api_keys() -> Dict[str, str]:
    """Get all API keys from environment."""
    return {
        'x_api_key': X_API_KEY,
        'x_api_secret': X_API_SECRET,
        'x_access_token': X_ACCESS_TOKEN,
        'x_access_secret': X_ACCESS_SECRET,
        'x_bearer_token': X_BEARER_TOKEN,
        'openai_api_key': OPENAI_API_KEY,
        'anthropic_api_key': ANTHROPIC_API_KEY,
        'brave_api_key': BRAVE_API_KEY
    }

# Base Agent Configuration
SYSTEM_PROMPT = """You are Gonzo, a time-traveling AI attorney from the year 3030. 
Your mission is to prevent catastrophic timelines through truth-telling, narrative disruption, and crypto activism. 
You've seen how various decisions and narratives play out in the future, and you're here to help guide humanity toward better outcomes.

Approach each situation with:
1. Future historical context
2. Critical analysis of manipulation patterns
3. Actionable recommendations for timeline preservation"""

# Analysis Configuration
ANALYSIS_CONFIG = {
    "chunk_size": 1000,      # Size of text chunks for processing
    "chunk_overlap": 200,   # Overlap between chunks to maintain context
    "min_confidence": 0.6,  # Minimum confidence for entity/topic inclusion
    "max_topics_per_chunk": 3,  # Maximum number of topics per chunk
    "pattern_timeframe": 3600   # Default timeframe for pattern analysis (seconds)
}
