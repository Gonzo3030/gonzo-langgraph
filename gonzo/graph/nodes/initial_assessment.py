from typing import Dict, Any, TypeVar, Optional
from langchain_core.messages import BaseMessage
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langsmith import traceable
from langchain_core.runnables import RunnableConfig
from ...config import MODEL_NAME
from ...types.base import GonzoState
from .base import update_state, log_step, get_latest_message

StateType = TypeVar("StateType")

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
async def initial_assessment(state: GonzoState, config: Optional[RunnableConfig] = None) -> Dict[str, GonzoState]:
    """Perform initial assessment of user input."""
    try:
        # Get latest message
        latest_message = get_latest_message(state)
        if not latest_message:
            raise ValueError("No message found in state")
        
        # Get LLM assessment
        chain = ASSESSMENT_PROMPT | llm
        result = await chain.ainvoke(
            {"input": latest_message.content},
            config=config
        )
        
        # Extract category and update state
        category = _extract_category(result.content)
        
        # Log step
        log_step(state, "initial_assessment", {
            "category": category,
            "assessment": result.content
        })
        
        # Return state dict
        return {"state": state}
        
    except Exception as e:
        state.add_error(f"Error in initial assessment: {str(e)}")
        return {"state": state}

def _extract_category(assessment: str) -> str:
    """Extract category from assessment result."""
    assessment_lower = assessment.lower()
    if "crypto" in assessment_lower:
        return "crypto"
    elif "narrative" in assessment_lower:
        return "narrative"
    return "general"