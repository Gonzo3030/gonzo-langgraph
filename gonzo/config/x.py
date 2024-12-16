"""X (Twitter) integration configuration."""

import os

X_API_KEY = os.getenv('X_API_KEY')
X_API_SECRET = os.getenv('X_API_SECRET')
X_ACCESS_TOKEN = os.getenv('X_ACCESS_TOKEN')
X_ACCESS_SECRET = os.getenv('X_ACCESS_SECRET')

# Monitoring configuration
MONITORED_KEYWORDS = [
    'bitcoin', 'ethereum', 'crypto',
    'dystopia', 'surveillance',
    'manipulation', 'narrative',
    'resistance', 'freedom'
]

MONITORED_ACCOUNTS = [
    # Add relevant accounts here
]

# Rate limiting and retries
RATE_LIMIT_DELAY = 60  # seconds
MAX_RETRIES = 3
MAX_THREAD_LENGTH = 10
MIN_CONFIDENCE = 0.8  # Minimum confidence for automated responses