"""X (Twitter) configuration settings."""

import os

# API credentials from environment
X_API_KEY = os.getenv('X_API_KEY')
X_API_SECRET = os.getenv('X_API_SECRET')
X_ACCESS_TOKEN = os.getenv('X_ACCESS_TOKEN')
X_ACCESS_SECRET = os.getenv('X_ACCESS_SECRET')

# Monitoring configuration
MONITORED_KEYWORDS = [
    'bitcoin', 'ethereum', 'crypto',
    'central bank', 'fed', 'cbdc',
    'web3', 'defi', 'dao',
    'narrative control', 'propaganda', 'manipulation'
]

MONITORED_ACCOUNTS = [
    # Add specific accounts to monitor
]

# Rate limiting and retry settings
RATE_LIMIT_DELAY = 60  # seconds
MAX_RETRIES = 3
MAX_THREAD_LENGTH = 10
MIN_CONFIDENCE = 0.8