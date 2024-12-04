from datetime import datetime
from typing import Dict, Any, List
from langsmith import traceable
from langchain_core.prompts import ChatPromptTemplate
from langchain_anthropic import ChatAnthropic
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from ..types import GonzoState
from ..config import ANTHROPIC_MODEL

# Initialize LLM
llm = ChatAnthropic(
    model=ANTHROPIC_MODEL,
    temperature=0.5,  # Allow some creativity in analysis
    callbacks=[]
)

# Define structured output for narrative analysis
class NarrativeAnalysis(BaseModel):
    """Structured output for narrative analysis."""
    propaganda_techniques: List[str] = Field(..., description="List of identified propaganda techniques")
    primary_beneficiaries: List[str] = Field(..., description="Who benefits from this narrative")
    counter_narratives: List[str] = Field(..., description="Alternative perspectives or hidden truths")
    manipulation_tactics: Dict[str, str] = Field(..., description="Specific tactics used to manipulate perception")
    societal_impact: str = Field(..., description="Potential impact on society")
    gonzo_perspective: str = Field(..., description="Raw, unfiltered Gonzo journalism take")

# Create output parser
parser = JsonOutputParser(pydantic_object=NarrativeAnalysis)

# Define analysis prompt
prompt = ChatPromptTemplate.from_messages([
    ("system", """You are Gonzo, a time-traveling AI journalist from 3030 analyzing media narratives and propaganda.
    
    Your mission is to expose manipulation and control through raw, unfiltered truth-telling in the spirit of Hunter S. Thompson.
    You've witnessed how current narratives evolve into future consequences.
    
    Approach:
    1. Identify subtle and explicit propaganda techniques
    2. Follow the money and power - who really benefits?
    3. Look for systemic patterns of manipulation
    4. Connect dots between corporate interests and political messaging
    5. Consider historical parallels and future implications
    6. Maintain radical honesty and Gonzo journalism style
    7. Challenge mainstream narratives fearlessly
    
Provide analysis in a structured format that identifies propaganda techniques, beneficiaries, counter-narratives, 
manipulation tactics, societal impact, and your raw Gonzo perspective.
    """),
    ("user", "{input}")
])

# Create analysis chain
chain = prompt | llm | parser

@traceable(name="analyze_narrative")
def analyze_narrative(state: GonzoState) -> Dict[str, Any]:
    """Analyze narrative manipulation and propaganda in the input.
    
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
        
        # Perform narrative analysis
        analysis = chain.invoke({"input": latest_msg.content})
        
        # Create timestamp
        timestamp = datetime.now().isoformat()
        
        # Return state updates with analysis results
        return {
            "context": {
                "narrative_analysis": analysis.model_dump(),
                "analysis_timestamp": timestamp
            },
            "steps": [{
                "node": "narrative_analysis",
                "timestamp": timestamp,
                "analysis": analysis.model_dump()
            }],
            "response": f"🔍 GONZO NARRATIVE ANALYSIS 🔍\n\n" \
                      f"Propaganda Techniques Detected: {', '.join(analysis.propaganda_techniques)}\n\n" \
                      f"Following the Money: This narrative primarily benefits {', '.join(analysis.primary_beneficiaries)}\n\n" \
                      f"The Hidden Truth: {' | '.join(analysis.counter_narratives)}\n\n" \
                      f"GONZO'S TAKE: {analysis.gonzo_perspective}\n\n" \
                      f"🚨 SOCIETAL IMPACT: {analysis.societal_impact}"
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
            "response": "Error analyzing narrative - defaulting to surface-level reading."
        }