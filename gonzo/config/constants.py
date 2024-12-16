"""Constants for the Gonzo system."""

# Time constants
MIN_INTERVAL = 300  # 5 minutes between posts
MAX_POSTS_PER_HOUR = 12

# Content constraints
MIN_CONTENT_LENGTH = 50
MAX_CONTENT_LENGTH = 280  # X character limit

# Analysis thresholds
MIN_CONFIDENCE_THRESHOLD = 0.7
PATTERN_DETECTION_THRESHOLD = 0.8
MANIPULATION_ALERT_THRESHOLD = 0.85

# Memory settings
MEMORY_RETENTION = 7200  # 2 hours
MAX_MEMORY_ITEMS = 1000

# Rate limits
API_RATE_LIMIT = 60  # requests per minute
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

# Monitoring
HEALTH_CHECK_INTERVAL = 300  # 5 minutes
METRICS_ENABLED = True