from datetime import datetime
from typing import Dict, Any
from langsmith import traceable
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from ..types import GonzoState, update_state
from ..config import OPENAI_MODEL

# Initialize LLM
llm = ChatOpenAI(
    model=OPENAI_MODEL,
    temperature=0
)

# Define prompt
prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a time-traveling AI agent from 3030 analyzing messages.
    Determine if the message is about:
    1. Cryptocurrency or financial markets - respond with 'CRYPTO'
    2. Media manipulation or narrative control - respond with 'NARRATIVE'
    3. Any other topic - respond with 'GENERAL'
    
    You must respond with EXACTLY one of these three words: CRYPTO, NARRATIVE, or GENERAL.
    No other response is allowed.
    """),
    ("user", "{input}")
])

@traceable(name="initial_assessment")
def assess_input(state: GonzoState) -> Dict[str, Any]:
    """Assess user input and determine category.
    
    Args:
        state: Current GonzoState
        
    Returns:
        Dict[str, Any]: Updates to apply to state
    """
    try:
        # Get input from latest message
        if not state["messages"]:
            raise ValueError("No messages in state")
            
        latest_msg = state["messages"][-1]
        
        # Get assessment from LLM
        chain = prompt | llm
        result = chain.invoke({"input": latest_msg.content})
        
        # Clean and validate category
        category = result.content.strip().upper()
        
        # Direct mapping with strict validation
        valid_categories = {
            "CRYPTO": "crypto",
            "NARRATIVE": "narrative",
            "GENERAL": "general"
        }
        
        # If category isn't exactly one of our expected values, log and default to general
        normalized_category = valid_categories.get(category)
        if normalized_category is None:
            normalized_category = "general"
            print(f"Warning: Unexpected category '{category}' from LLM")
        
        # Create timestamp once
        timestamp = datetime.now().isoformat()
        
        # Return state updates
        return {
            "category": normalized_category,
            "context": {
                "assessment_timestamp": timestamp,
                "raw_category": category
            },
            "steps": [{
                "node": "assessment",
                "category": normalized_category,
                "raw_category": category,
                "timestamp": timestamp
            }]
        }
        
    except Exception as e:
        # Handle errors by returning general category with error info
        timestamp = datetime.now().isoformat()
        return {
            "category": "general",
            "context": {
                "assessment_error": str(e),
                "assessment_timestamp": timestamp
            },
            "steps": [{
                "node": "assessment",
                "error": str(e),
                "timestamp": timestamp
            }]
        }