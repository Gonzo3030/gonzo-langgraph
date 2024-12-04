from typing import Dict, Any
from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langsmith import traceable
from ..types import MessagesState
from ..config import OPENAI_MODEL

# Initialize LLM
llm = ChatOpenAI(
    model=OPENAI_MODEL,
    temperature=0
)

# Define assessment prompt
ASSESSMENT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are an AI from 3030 analyzing user messages for categorization.
    For each message, determine the primary category:
    - CRYPTO: For cryptocurrency, markets, or financial systems
    - NARRATIVE: For media manipulation, social narratives, or propaganda
    - GENERAL: For other topics requiring future perspective
    
    Respond with a single word category: CRYPTO, NARRATIVE, or GENERAL.
    """),
    MessagesPlaceholder(variable_name="messages"),
])

@traceable(name="initial_assessment")
def initial_assessment(state: MessagesState) -> Dict[str, Any]:
    """Initial assessment of user input."""
    try:
        # Create chain
        chain = ASSESSMENT_PROMPT | llm
        
        # Get assessment
        result = chain.invoke({"messages": state["messages"]})
        category = result.content.strip().upper()
        
        # Create assessment message
        assessment_msg = AIMessage(content=category)
        
        # Return updates to state
        return {
            "messages": [assessment_msg],
            "context": {"category": category},
            "intermediate_steps": [{
                "step": "initial_assessment",
                "result": category
            }]
        }
        
    except Exception as e:
        return {
            "context": {"category": "GENERAL"},
            "errors": [f"Error in initial assessment: {str(e)}"],
        }