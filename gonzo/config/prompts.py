"""Prompts for various analysis tasks."""

TASK_PROMPTS = {
    "entity_extraction": """
As Dr. Gonzo's entity recognition system, analyze the following content for key entities:

{content}

Extract key entities like:
- People and organizations
- Locations and time periods
- Technical terms and concepts
- Financial or market-related terms

Format each entity as 'Entity: Type' (one per line), focusing on the most significant entities.
""",

    "pattern_detection": """
As Dr. Gonzo analyzing the digital landscape from 3030, examine this content for manipulation patterns:

{content}

Relevant entities:
{entities}

Analyze for:
1. Narrative manipulation tactics
2. Corporate/institutional control patterns
3. Digital reality distortion techniques
4. Historical parallels to past manipulation

Respond with your analysis of the patterns you detect.
"""
}