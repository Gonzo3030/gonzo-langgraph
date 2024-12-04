from typing import Dict, Any
from langchain_core.messages import BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langsmith import traceable
from ..types import AgentState
from ..config import OPENAI_MODEL

# Initialize LLM
llm = ChatOpenAI(
    model=OPENAI_MODEL,
    temperature=0,
    verbose=True
)

# Define assessment prompt
ASSESSMENT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are an AI from 3030 analyzing user messages for categorization.
    Analyze the latest message and categorize it based on these criteria:
    - CRYPTO: Discussions about cryptocurrency, markets, or financial systems
    - NARRATIVE: Discussions about media manipulation, social narratives, or propaganda
    - GENERAL: Other topics requiring your future perspective
    
    For each message, assess urgency and potential impact on future timelines.
    """),
    MessagesPlaceholder(variable_name="messages"),
])

@traceable(name="initial_assessment")
def initial_assessment(state: AgentState) -> AgentState:
    """Initial assessment of user input."""
    try:
        # Create chain
        chain = ASSESSMENT_PROMPT | llm
        
        # Get assessment
        result = chain.invoke({"messages": state.messages})
        
        # Process result and update state
        new_state = state.model_copy()
        new_state.context["assessment"] = result.content
        new_state.context["category"] = _extract_category(result.content)
        new_state.intermediate_steps.append({
            "step": "initial_assessment",
            "result": result.content
        })
        
        return new_state
        
    except Exception as e:
        # Handle errors properly with Pydantic state
        new_state = state.model_copy()
        new_state.errors.append(f"Error in initial assessment: {str(e)}")
        new_state.context["category"] = "general"
        return new_state

def _extract_category(assessment: str) -> str:
    """Extract category from assessment result."""
    assessment_lower = assessment.lower()
    if "crypto" in assessment_lower or "bitcoin" in assessment_lower:
        return "crypto"
    elif "narrative" in assessment_lower or "manipulation" in assessment_lower:
        return "narrative"
    return "general"