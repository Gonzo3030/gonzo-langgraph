"""Configuration for content analysis."""

ANALYSIS_CONFIG = {
    # Content processing
    "chunk_size": 1000,
    "chunk_overlap": 200,
    
    # Pattern detection
    "min_pattern_confidence": 0.6,
    "max_patterns_per_analysis": 5,
    
    # Time periods
    "time_periods": [
        "counterculture",   # 1965-1974
        "digital_transition", # 1974-1999
        "present",          # 2024
        "future"            # 3030
    ],
    
    # Response generation
    "max_quick_take_length": 280,  # Twitter character limit
    "max_thread_length": 2800,    # 10 tweets worth
    "max_bridge_length": 560,     # 2 tweets worth
    
    # Evolution parameters
    "evolution_decay_rate": 0.8,   # How fast old patterns decay
    "min_significance": 0.3,      # Minimum significance for patterns
    
    # Memory settings
    "max_memory_age_days": 30,    # How long to keep detailed memory
    "memory_summarize_threshold": 50  # When to summarize old memories
}