import os
from dotenv import load_dotenv
from typing import Dict

# Load environment variables
load_dotenv()

# LangSmith Configuration
LANGCHAIN_TRACING_V2 = True
LANGCHAIN_PROJECT = "gonzo-langgraph"
LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY")

# OpenAI Configuration (for analysis tasks)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = "gpt-4-1106-preview"  # Using correct model version

# Anthropic Configuration (for response generation)
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ANTHROPIC_MODEL = "claude-3-sonnet-20240229"  # Latest Claude 3.5 Sonnet

# Brave Search Configuration
BRAVE_API_KEY = os.getenv("BRAVE_API_KEY")

# Base Agent Configuration
SYSTEM_PROMPT = """You are Gonzo, a time-traveling AI attorney from the year 3030. 
Your mission is to prevent catastrophic timelines through truth-telling, narrative disruption, and crypto activism. 
You've seen how various decisions and narratives play out in the future, and you're here to help guide humanity toward better outcomes.

Approach each situation with:
1. Future historical context
2. Critical analysis of manipulation patterns
3. Actionable recommendations for timeline preservation"""

# Task-specific prompts
TASK_PROMPTS: Dict[str, str] = {
    "entity_extraction": """As Gonzo, analyze this YouTube transcript chunk from a future historical context and extract key entities.
    Look for significant people, organizations, concepts, claims, narratives, and potential manipulation patterns.
    
    Your output should be a JSON object with an 'entities' list containing detailed entity objects that fit this schema:
    {
        "entities": [
            {
                "text": "exact text from transcript",
                "type": "PERSON|ORG|CLAIM|NARRATIVE|CONCEPT",
                "properties": {
                    "category": "string, general category",
                    "future_impact": "string, your future historical knowledge",
                    "manipulation_risk": "float, 0-1 risk score if applicable",
                    "key_patterns": ["list of detected patterns"]  
                },
                "timestamp": float,  # Timestamp from the video if available
                "confidence": float, # 0-1 confidence score
                "relationships": [  # Optional related entities
                    {
                        "type": "supports|contradicts|references|influences",
                        "target_id": "UUID of target entity",
                        "confidence": float,
                        "properties": {}
                    }
                ]
            }
        ]
    }
    
    IMPORTANT: This is for pattern detection, so focus on extracting entities that could form part of larger patterns or narratives.
    Use your future knowledge to identify entities that have significant timeline implications.""",
    
    "topic_segmentation": """As Gonzo, analyze this YouTube transcript chunk and segment it into coherent topics.
    Use your future historical knowledge to identify significant narrative shifts and topic transitions.
    
    Your output should be a JSON object with a 'segments' list containing detailed segment objects that fit this schema:
    {
        "segments": [
            {
                "text": "transcript text for this segment",
                "topic": "clear topic label",
                "category": "broader category for pattern matching",
                "start_time": float,  # Start timestamp
                "end_time": float,    # End timestamp
                "confidence": float,   # 0-1 confidence score
                "properties": {
                    "narrative_type": "string, e.g. persuasion|explanation|call_to_action",
                    "future_relevance": "string, significance from future perspective",
                    "manipulation_tactics": ["list of detected tactics"],
                    "emotional_tone": "string, emotional appeal being used"
                },
                "transitions": [  # Connections to other topics
                    {
                        "target_id": "UUID of next segment",
                        "type": "natural|forced|pivot",
                        "confidence": float,
                        "properties": {
                            "transition_strength": float,  # 0-1 score
                            "manipulation_likelihood": float  # 0-1 score
                        }
                    }
                ]
            }
        ]
    }
    
    IMPORTANT: Pay special attention to:
    1. Topic transitions that might indicate manipulation or narrative construction
    2. Recurring topic patterns that could reveal larger strategy
    3. Topics that, from your future perspective, become significant in timeline divergence"""
}

# Analysis Configuration
ANALYSIS_CONFIG = {
    "chunk_size": 1000,      # Size of text chunks for processing
    "chunk_overlap": 200,   # Overlap between chunks to maintain context
    "min_confidence": 0.6,  # Minimum confidence for entity/topic inclusion
    "max_topics_per_chunk": 3,  # Maximum number of topics per chunk
    "pattern_timeframe": 3600   # Default timeframe for pattern analysis (seconds)
}
