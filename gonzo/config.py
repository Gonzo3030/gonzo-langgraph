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

# News Monitoring Configuration
NEWS_CONFIG = {
    "update_frequency": 5,    # Update news every N cycles
    "max_articles": 20,      # Maximum articles per search
    "time_window": "7d",     # Look back period for news
    "min_relevance": 0.4,    # Minimum relevance score for articles
    "relevance_boost": {     # Relevance score boosts
        "whale_movement": 0.3,
        "market_manipulation": 0.3,
        "bot_activity": 0.2,
        "regulatory": 0.1
    },
    "search_topics": [       # Primary search topics
        "crypto whale movements",
        "bitcoin manipulation",
        "crypto trading bots",
        "market manipulation crypto",
        "suspicious crypto transactions",
        "large bitcoin transfers"
    ],
    "asset_keywords": [      # Assets to track in news
        "bitcoin", "btc",
        "ethereum", "eth",
        "crypto", "cryptocurrency",
        "digital assets", "blockchain"
    ]
}

# Graph Configuration
GRAPH_CONFIG = {
    "max_retries": 3,
    "retry_delay": 5,
    "error_threshold": 0.3,  # Maximum error rate before triggering recovery
    "cycle_delay": 60,      # Delay between monitoring cycles (seconds)
    "news_cycle": 5,       # News update frequency (cycles)
    "recursion_limit": 100,  # Maximum recursion depth for workflow
    "cycle_timeout": 300   # Maximum time for a single cycle (seconds)
}

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