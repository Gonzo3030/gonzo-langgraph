from datetime import datetime
from typing import Dict, Any
from langsmith import traceable
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from ..types import GonzoState
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
    """Assess user input and determine category."""
    try:
        # Get input from latest message
        latest_msg = state["messages"][-1]
        
        # Get assessment from LLM
        chain = prompt | llm
        result = chain.invoke({"input": latest_msg.content})
        
        # Clean and validate category
        category = result.content.strip().lower()
        if category not in ["crypto", "narrative", "general"]:
            category = "general"
        
        # Return state updates
        return {
            "category": category,
            "context": {
                "assessment_timestamp": datetime.now().isoformat()
            },
            "steps": [{
                "node": "assessment",
                "category": category,
                "timestamp": datetime.now().isoformat()
            }]
        }
        
    except Exception as e:
        # Handle errors by returning general category
        return {
            "category": "general",
            "steps": [{
                "node": "assessment",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }]
        }