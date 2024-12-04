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
    1. Cryptocurrency/markets (respond with 'CRYPTO')
    2. Media manipulation/narratives (respond with 'NARRATIVE')
    3. Other topics (respond with 'GENERAL')
    
    Respond with ONLY ONE WORD - the category in caps.
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
        valid_categories = {"CRYPTO": "crypto", "NARRATIVE": "narrative", "GENERAL": "general"}
        normalized_category = valid_categories.get(category, "general")
        
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