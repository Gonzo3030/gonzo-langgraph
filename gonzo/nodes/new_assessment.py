from typing import Dict, Any
from datetime import datetime
from langsmith import traceable
from langchain_core.prompts import ChatPromptTemplate
from langchain_anthropic import ChatAnthropic
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableParallel, RunnablePassthrough

from ..graph.state import GonzoState
from ..config import ANTHROPIC_MODEL

# Initialize LLM with tracing
llm = ChatAnthropic(
    model=ANTHROPIC_MODEL,
    temperature=0
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
    ("user", "{content}")
])

# Create assessment chain
assessment_chain = RunnableParallel(
    output=prompt | llm | StrOutputParser()
).with_types(input_type=Dict)

@traceable(name="assess_input")
async def assess_input(state: GonzoState) -> Dict[str, Any]:
    """Assess user input and determine category.
    
    Args:
        state: GonzoState object containing the current state
        
    Returns:
        Dict containing the next step and updated state information
    """
    try:
        if not state.state['messages']:
            state.add_error("No messages in state")
            state.set_next_step('error')
            return {"next": "error"}
            
        latest_msg = state.state['messages'][-1]
        
        # Get category from LLM using the assessment chain
        result = await assessment_chain.ainvoke({"content": latest_msg.content})
        category = result["output"].strip().upper()
        
        # Validate and normalize category
        valid_categories = {
            "CRYPTO": "crypto",
            "NARRATIVE": "narrative",
            "GENERAL": "general"
        }
        
        normalized_category = valid_categories.get(category, "general")
        timestamp = datetime.now().isoformat()
        
        # Save assessment results to memory
        assessment_result = {
            "category": normalized_category,
            "raw_category": category,
            "timestamp": timestamp,
            "message_content": latest_msg.content
        }
        
        state.save_to_memory(
            key="last_assessment",
            value=assessment_result
        )
        
        # Set next step based on category
        if normalized_category == "crypto":
            state.set_next_step("crypto")
            return {"next": "crypto"}
        elif normalized_category == "narrative":
            state.set_next_step("narrative")
            return {"next": "narrative"}
        else:
            state.set_next_step("general")
            return {"next": "general"}
            
    except Exception as e:
        error_msg = f"Assessment error: {str(e)}"
        state.add_error(error_msg)
        state.save_to_memory(
            key="last_error",
            value={
                "error": error_msg,
                "timestamp": datetime.now().isoformat(),
                "node": "assessment"
            }
        )
        state.set_next_step("error")
        return {"next": "error"}