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
    ("system", """You are analyzing user queries as a time-traveling AI agent from 3030.
    Return the category and assessment of the query in the following format:
    CATEGORY: [crypto/narrative/general]
    ASSESSMENT: [brief explanation]
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
        
        # Extract category from response
        response_lines = result.content.split("\n")
        category = response_lines[0].split(":")[1].strip().lower()
        assessment = response_lines[1].split(":")[1].strip()
        
        # Return state updates
        return {
            "category": category,
            "context": {
                "assessment": assessment,
                "timestamp": datetime.now().isoformat()
            },
            "steps": [{
                "node": "assessment",
                "category": category,
                "assessment": assessment,
                "timestamp": datetime.now().isoformat()
            }]
        }
        
    except Exception as e:
        # Handle errors gracefully
        return {
            "category": "general",
            "steps": [{
                "node": "assessment", 
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }]
        }