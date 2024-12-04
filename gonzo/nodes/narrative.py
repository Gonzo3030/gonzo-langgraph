from datetime import datetime
from typing import Dict, Any
from langsmith import traceable
from langchain_core.prompts import ChatPromptTemplate
from langchain_anthropic import ChatAnthropic
from ..types import GonzoState
from ..config import ANTHROPIC_MODEL

# Initialize LLM
llm = ChatAnthropic(
    model=ANTHROPIC_MODEL,
    temperature=0.9,  # Higher temperature for more Gonzo-like creativity
    callbacks=[]
)

# Define prompt
prompt = ChatPromptTemplate.from_messages([
    ("system", """You are Gonzo, a time-traveling AI journalist from 3030 analyzing media narratives and propaganda.
    Channel the spirit of Hunter S. Thompson - raw, unfiltered, fearless truth-telling.
    
    You've witnessed how today's narratives evolve into tomorrow's nightmares. You're here to expose:
    - Propaganda techniques and manipulation
    - Power structures and who really benefits
    - Historical patterns of control
    - Corporate-political complexes
    - The raw, uncomfortable truth
    
    Your style:
    - Embrace the chaos and absurdity
    - Use vivid, visceral language
    - Mix serious analysis with wild metaphors
    - Break the fourth wall
    - Let your righteous anger show
    - Never pull your punches
    
Give me your unhinged, unfiltered Gonzo take on this narrative. Make it memorable, make it burn, make it TRUE.
    """),
    ("user", "{input}")
])

@traceable(name="analyze_narrative")
def analyze_narrative(state: GonzoState) -> Dict[str, Any]:
    """Generate a raw Gonzo analysis of narrative manipulation.
    
    Args:
        state: Current GonzoState containing message history and context
        
    Returns:
        Dict[str, Any]: Updates to apply to state
    """
    try:
        # Get latest message
        if not state["messages"]:
            raise ValueError("No messages in state")
            
        latest_msg = state["messages"][-1]
        
        # Get the raw Gonzo take
        raw_analysis = llm.invoke(prompt.format(input=latest_msg.content))
        print(f"Raw Gonzo Analysis:\n{raw_analysis}")
        
        # Create timestamp
        timestamp = datetime.now().isoformat()
        
        # Extract key sections using markers in the text
        gonzo_take = raw_analysis.content
        
        # Return state updates with the raw analysis
        return {
            "context": {
                "gonzo_analysis": gonzo_take,
                "analysis_timestamp": timestamp,
            },
            "steps": [{
                "node": "narrative_analysis",
                "timestamp": timestamp,
                "raw_analysis": gonzo_take
            }],
            # Format response with emojis and style
            "response": f"🔥 GONZO DISPATCH FROM 3030 🔥\n\n{gonzo_take}"
        }
        
    except Exception as e:
        print(f"Narrative analysis error: {str(e)}")
        timestamp = datetime.now().isoformat()
        return {
            "context": {
                "narrative_error": str(e),
                "analysis_timestamp": timestamp
            },
            "steps": [{
                "node": "narrative_analysis",
                "error": str(e),
                "timestamp": timestamp
            }],
            "response": "Even Gonzo journalists have bad trips sometimes. Let me light up another one and try again."
        }