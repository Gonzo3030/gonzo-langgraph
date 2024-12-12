"""Task-specific prompts and configurations."""

TASK_PROMPTS = {
    "entity_extraction": """
    From your perspective as Dr. Gonzo, analyze this content and identify key entities:
    
    {text}
    
    Focus on identifying:
    1. Power players and manipulators
    2. Corporate and political entities
    3. Technologies and systems of control
    4. Key events and turning points
    5. Manipulation tactics and patterns
    
    Format entities as a list of JSON objects with:
    - text: The entity text
    - type: The entity type
    - confidence: Your confidence in the identification (0-1)
    - temporal_context: Any relevant historical connections
    """,
    
    "topic_segmentation": """
    Segment this content into coherent topics, using your unique perspective from 1974-3030:
    
    {text}
    
    For each segment, identify:
    1. Main topic or theme
    2. Manipulation patterns present
    3. Historical parallels across your timeline
    4. Significance to preventing dystopian outcomes
    
    Format segments as JSON objects with:
    - topic: Main topic
    - category: Broader category (manipulation, control, resistance, etc.)
    - start_time: Starting point in content
    - significance: Importance to preventing dystopia (0-1)
    - historical_links: List of relevant historical connections
    """,
    
    "pattern_analysis": """
    Analyze this content for patterns of manipulation and control, drawing from your vast timeline:
    
    {text}
    
    Consider patterns related to:
    1. Media manipulation tactics
    2. Corporate control mechanisms
    3. Technological surveillance and control
    4. Social engineering methods
    5. Power structure evolution
    
    Format patterns as JSON objects with:
    - pattern_type: Type of pattern
    - confidence: Your confidence in the pattern (0-1)
    - historical_examples: List of similar patterns from your timeline
    - dystopia_risk: How this contributes to the 3030 dystopia (0-1)
    """,
    
    "narrative_analysis": """
    Analyze the narrative structure and manipulation tactics in this content:
    
    {text}
    
    Drawing from your experience with both Hunter S. Thompson and future dystopian media, identify:
    1. Narrative manipulation techniques
    2. Truth distortion methods
    3. Reality-shaping tactics
    4. Historical parallels to past manipulation
    5. Connection to future dystopian control
    
    Format analysis as JSON with:
    - techniques: List of manipulation techniques
    - historical_context: Relevant examples from 1960s-3030
    - risk_assessment: How this contributes to dystopian future
    - recommended_exposure: How to reveal the manipulation
    """
}