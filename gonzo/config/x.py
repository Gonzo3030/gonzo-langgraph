"""X (Twitter) API configuration."""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Credentials
X_API_KEY = os.getenv("X_API_KEY")
X_API_SECRET = os.getenv("X_API_SECRET")
X_ACCESS_TOKEN = os.getenv("X_ACCESS_TOKEN")
X_ACCESS_SECRET = os.getenv("X_ACCESS_SECRET")
X_BEARER_TOKEN = os.getenv("X_BEARER_TOKEN")

# Rate Limiting Configuration
X_MAX_RETRIES = 3
X_BASE_DELAY = 5  # Base delay in seconds for exponential backoff
X_MAX_DELAY = 300  # Maximum delay in seconds
RATE_LIMIT_DELAY = 60  # Default delay when rate limited

# Monitoring Configuration
MAX_RETRIES = 3
MAX_THREAD_LENGTH = 100
MIN_CONFIDENCE = 0.6

# Content to monitor
MONITORED_KEYWORDS = [
    "manipulation",
    "timeline disruption",
    "crypto activism",
    "dystopian future",
    "timeline preservation"
]

MONITORED_ACCOUNTS = [
    "@Gonzo_3030"
]