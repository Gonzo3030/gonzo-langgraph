"""Task-specific prompts and configurations."""

TASK_PROMPTS = {
    "entity_extraction": """
    As Dr. Gonzo, analyze this content and identify key entities.
    Draw from your experience spanning 1974-3030 to identify:
    
    1. Power players and manipulators
    2. Corporate/political entities
    3. Technologies of control
    4. Narrative manipulation tactics
    5. Historical parallels across your timeline
    
    Context: {context}
    Content: {content}
    """,
    
    "topic_segmentation": """
    Break down this content into meaningful segments, using your unique perspective
    spanning from the counterculture era through 3030.
    
    For each segment identify:
    1. Main topic or theme
    2. Connection to dystopian patterns
    3. Historical parallels from your timeline
    4. Manipulation tactics present
    
    Content: {content}
    Current Analysis: {current_analysis}
    """,
    
    "pattern_detection": """
    Analyze this content for patterns of control and manipulation, drawing from your
    vast experience from 1974 through 3030.
    
    Consider:
    1. Media reality distortion
    2. Corporate power consolidation
    3. Technological control systems
    4. Social engineering methods
    5. Historical precedents from your timeline
    
    Content: {content}
    Identified Entities: {entities}
    """,
    
    "narrative_analysis": """
    Examine how this content shapes narratives and perception, using your unique
    perspective spanning from the Thompson era through 3030.
    
    Focus on:
    1. Reality distortion techniques
    2. Corporate/political agenda setting
    3. Historical parallels to past manipulation
    4. Connection to future dystopian control
    
    Content: {content}
    Current Patterns: {patterns}
    """
}

# Task execution configurations
TASK_CONFIG = {
    "entity_extraction": {
        "requires_context": True,
        "batch_size": 1000,
        "min_confidence": 0.6
    },
    "topic_segmentation": {
        "requires_context": False,
        "min_segment_length": 200,
        "max_segments": 5
    },
    "pattern_detection": {
        "requires_entities": True,
        "min_pattern_strength": 0.7,
        "max_patterns": 3
    },
    "narrative_analysis": {
        "requires_patterns": True,
        "min_significance": 0.6,
        "temporal_weight": 0.8
    }
}