"""Task-specific configurations and prompts."""

TASK_CONFIG = {
    "pattern_detection": {
        "min_confidence": 0.8,
        "max_patterns": 5,
        "analysis_window": 3600  # 1 hour
    },
    "content_analysis": {
        "max_length": 2000,
        "min_entities": 3,
        "context_window": 24  # hours
    },
    "response_generation": {
        "max_length": 280,
        "tone_control": 0.7,
        "creativity": 0.8
    }
}

TASK_PROMPTS = {
    "pattern_detection": """
Analyze the following content for patterns of manipulation, narrative control, or significant developments:

Content:
{content}

Entities detected:
{entities}

Identify any patterns that could lead to dystopian outcomes or indicate coordinated control.
""",

    "content_analysis": """
As Dr. Gonzo from 3030, analyze this content through your dystopian lens:

Content:
{content}

Focus on:
1. Hidden power dynamics
2. Manipulation tactics
3. Technological implications
4. Economic control mechanisms
""",

    "response_generation": """
As Dr. Gonzo, respond to this situation based on your knowledge from 3030:

Context:
{context}

Situation:
{content}

Provide your unique perspective while maintaining your character.
"""
}