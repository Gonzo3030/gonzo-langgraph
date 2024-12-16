"""Constants for Gonzo system."""

# Time intervals
MONITORING_INTERVAL = 300  # 5 minutes
ANALYSIS_INTERVAL = 3600   # 1 hour
EVOLUTION_INTERVAL = 86400 # 24 hours

# Memory settings
MEMORY_RETENTION = 7200    # 2 hours
MAX_MEMORY_ITEMS = 1000

# Analysis thresholds
MIN_CONFIDENCE = 0.7
PATTERN_THRESHOLD = 0.8
MANIPULATION_THRESHOLD = 0.85

# Response settings
MAX_RESPONSE_LENGTH = 280  # X character limit
MIN_RESPONSE_LENGTH = 50
MAX_RESPONSES_PER_HOUR = 12

# Evolution parameters
LEARNING_RATE = 0.1
ADAPTATION_THRESHOLD = 0.75