from typing import Dict, Any
from langchain_core.messages import BaseMessage
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langsmith import traceable
from ..types import GonzoState
from ..config import OPENAI_MODEL

# Initialize LLM
llm = ChatOpenAI(model=OPENAI_MODEL, temperature=0)  # Set temperature to 0 for consistent testing

# Define prompt template
ASSESSMENT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are an AI from 3030 analyzing user queries. Respond with a JSON-like structure containing:
    {{
        "category": "crypto|narrative|general",
        "urgency": "high|medium|low",
        "complexity": "high|medium|low",
        "timeline_impact": "high|medium|low",
        "reasoning": "brief explanation"
    }}
    
    Guidelines:
    - crypto: For cryptocurrency, markets, or financial systems
    - narrative: For media manipulation, social narratives, or propaganda
    - general: For other topics requiring future perspective
    """),
    ("human", "{input}")
])

@traceable(name="initial_assessment")
def initial_assessment(state: GonzoState) -> GonzoState:
    """Perform initial assessment of user input."""
    try:
        # Create a new state copy with initialized context
        new_state = state.copy()
        if "context" not in new_state:
            new_state["context"] = {}

        # Get latest message
        latest_message = new_state["messages"][-1]
        
        # Get LLM assessment
        chain = ASSESSMENT_PROMPT | llm
        result = chain.invoke({"input": latest_message.content})
        
        # Update state with assessment
        assessment_content = result.content
        new_state["context"]["assessment"] = assessment_content
        new_state["context"]["category"] = _extract_category(assessment_content)
        new_state["intermediate_steps"].append({
            "step": "initial_assessment",
            "result": assessment_content
        })
        
        return new_state
        
    except Exception as e:
        # Handle errors gracefully
        new_state = state.copy()
        if "context" not in new_state:
            new_state["context"] = {}
        new_state["context"]["category"] = "general"  # Default to general on error
        new_state["errors"].append(f"Error in initial assessment: {str(e)}")
        return new_state

def _extract_category(assessment: str) -> str:
    """Extract category from assessment result."""
    assessment_lower = assessment.lower()
    if "crypto" in assessment_lower:
        return "crypto"
    elif "narrative" in assessment_lower:
        return "narrative"
    return "general"