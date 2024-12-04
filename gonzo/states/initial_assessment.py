from typing import Dict, Any
from langchain_core.messages import BaseMessage
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langsmith import traceable
from ..types import GonzoState
from ..config import OPENAI_MODEL
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize LLM
llm = ChatOpenAI(
    model=OPENAI_MODEL,
    temperature=0,
    verbose=True  # Enable verbose output
)

# Define prompt template
ASSESSMENT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are an AI from 3030 analyzing user queries.
    
    INSTRUCTIONS:
    1. Analyze the user's message
    2. Determine the primary category based on these criteria:
       - CRYPTO: If about cryptocurrency, markets, or financial systems
       - NARRATIVE: If about media manipulation, social narratives, or propaganda
       - GENERAL: If about other topics
    3. Respond in this exact JSON format:
    {
        "category": "CRYPTO|NARRATIVE|GENERAL",
        "confidence": "HIGH|MEDIUM|LOW",
        "reasoning": "Brief explanation of categorization"
    }
    """)
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
        logger.debug(f"Processing message: {latest_message.content}")
        
        # Get LLM assessment
        chain = ASSESSMENT_PROMPT | llm
        logger.debug("Calling LLM for assessment...")
        result = chain.invoke({"input": latest_message.content})
        logger.debug(f"LLM response: {result.content}")
        
        # Update state with assessment
        assessment_content = result.content
        new_state["context"]["assessment"] = assessment_content
        category = _extract_category(assessment_content)
        logger.debug(f"Extracted category: {category}")
        new_state["context"]["category"] = category
        new_state["intermediate_steps"].append({
            "step": "initial_assessment",
            "result": assessment_content
        })
        
        return new_state
        
    except Exception as e:
        logger.error(f"Error in initial assessment: {str(e)}", exc_info=True)
        new_state = state.copy()
        if "context" not in new_state:
            new_state["context"] = {}
        new_state["context"]["category"] = "general"  # Default to general on error
        new_state["errors"].append(f"Error in initial assessment: {str(e)}")
        return new_state

def _extract_category(assessment: str) -> str:
    """Extract category from assessment result."""
    try:
        assessment_lower = assessment.lower()
        if "crypto" in assessment_lower or "cryptocurrency" in assessment_lower:
            return "crypto"
        elif "narrative" in assessment_lower or "propaganda" in assessment_lower:
            return "narrative"
        return "general"
    except Exception as e:
        logger.error(f"Error extracting category: {str(e)}", exc_info=True)
        return "general"