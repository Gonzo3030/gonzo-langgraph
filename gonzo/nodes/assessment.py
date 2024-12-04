from datetime import datetime
from typing import Dict, Any
from langsmith import traceable
from langchain_core.prompts import ChatPromptTemplate
from langchain_anthropic import ChatAnthropic
from langchain_core.output_parsers import StrOutputParser
from ..types import GonzoState, update_state
from ..config import ANTHROPIC_MODEL

# Initialize LLM with tracing
llm = ChatAnthropic(
    model=ANTHROPIC_MODEL,
    temperature=0,
    callbacks=[]
)

# Define prompt
prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a time-traveling AI agent from 3030 analyzing messages.
    Your task is to classify the message into one of these categories:
    1. CRYPTO - for cryptocurrency, Bitcoin, or financial markets topics
    2. NARRATIVE - for media manipulation, narrative control, or social influence topics
    3. GENERAL - for any other topics
    
    Response rules:
    - You MUST respond with EXACTLY one word
    - Only these responses are allowed: CRYPTO, NARRATIVE, or GENERAL
    - Do not add any explanation or punctuation
    - Do not add any other words
    """),
    ("user", "{input}")
])

# Create chain with output parser
chain = prompt | llm | StrOutputParser()

@traceable(name="assess_input")
def assess_input(state: GonzoState) -> Dict[str, Any]:
    """Assess user input and determine category."""
    try:
        if not state["messages"]:
            raise ValueError("No messages in state")
            
        latest_msg = state["messages"][-1]
        
        # Get raw response for debugging
        raw_response = chain.invoke({"input": latest_msg.content})
        print(f"LLM Response: '{raw_response}'")
        
        # Clean and validate
        category = raw_response.strip().upper()
        valid_categories = {
            "CRYPTO": "crypto",
            "NARRATIVE": "narrative",
            "GENERAL": "general"
        }
        
        normalized_category = valid_categories.get(category, "general")
        if normalized_category == "general" and category not in valid_categories:
            print(f"Warning: Unexpected category '{category}' from LLM")
        
        timestamp = datetime.now().isoformat()
        
        return {
            "category": normalized_category,
            "context": {
                "assessment_timestamp": timestamp,
                "raw_category": category,
                "normalized_category": normalized_category
            },
            "steps": [{
                "node": "assessment",
                "category": normalized_category,
                "raw_category": category,
                "timestamp": timestamp
            }]
        }
        
    except Exception as e:
        print(f"Assessment error: {str(e)}")
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