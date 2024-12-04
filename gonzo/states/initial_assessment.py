from typing import Dict, Any
from langchain_core.messages import BaseMessage
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langsmith import traceable
from ..types import GonzoState
from ..config import MODEL_NAME

# Initialize LLM
llm = ChatOpenAI(model_name=MODEL_NAME)

# Define prompt template
ASSESSMENT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """As an AI from 3030, analyze the user's message and classify it into one of these categories:
    - crypto: Discussions about cryptocurrency, markets, or financial systems
    - narrative: Discussions about media manipulation, social narratives, or propaganda
    - general: Other topics requiring your time-traveled perspective
    
    Also assess:
    - Urgency: How time-critical is this query? (high/medium/low)
    - Complexity: How complex is the topic? (high/medium/low)
    - Timeline Impact: Potential impact on future timelines (high/medium/low)
    
    Provide your analysis in a structured format."""),
    ("human", "{input}")
])

@traceable(name="initial_assessment")
def initial_assessment(state: GonzoState) -> GonzoState:
    """Perform initial assessment of user input."""
    try:
        # Get latest message
        latest_message = state["messages"][-1]
        
        # Get LLM assessment
        chain = ASSESSMENT_PROMPT | llm
        result = chain.invoke({"input": latest_message.content})
        
        # Update state with assessment
        new_state = state.copy()
        new_state["context"]["assessment"] = result.content
        new_state["context"]["category"] = _extract_category(result.content)
        new_state["intermediate_steps"].append({
            "step": "initial_assessment",
            "result": result.content
        })
        
        return new_state
        
    except Exception as e:
        # Handle errors gracefully
        new_state = state.copy()
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