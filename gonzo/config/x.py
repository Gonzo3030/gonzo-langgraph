"""X API configuration."""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# X API Configuration
X_API_KEY = os.getenv("X_API_KEY")
X_API_SECRET = os.getenv("X_API_SECRET")
X_ACCESS_TOKEN = os.getenv("X_ACCESS_TOKEN")
X_ACCESS_SECRET = os.getenv("X_ACCESS_SECRET")

# Monitoring Configuration
MONITORED_KEYWORDS = [
    "crypto manipulation",
    "market manipulation",
    "narrative control",
    "digital dystopia",
    "corporate control"
]

MONITORED_ACCOUNTS = [
    "@DrGonzo3030"  # Gonzo's own account
]

# Rate Limiting
RATE_LIMIT_DELAY = 60  # seconds to wait when rate limited
MAX_RETRIES = 3  # maximum number of retry attempts

# Thread Configuration
MAX_THREAD_LENGTH = 10  # maximum number of tweets in a thread
MIN_CONFIDENCE = 0.7  # minimum confidence for pattern detection

__all__ = [
    'X_API_KEY',
    'X_API_SECRET',
    'X_ACCESS_TOKEN',
    'X_ACCESS_SECRET',
    'MONITORED_KEYWORDS',
    'MONITORED_ACCOUNTS',
    'RATE_LIMIT_DELAY',
    'MAX_RETRIES',
    'MAX_THREAD_LENGTH',
    'MIN_CONFIDENCE'
]