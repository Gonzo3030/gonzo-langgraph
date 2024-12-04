from typing import Dict, Any
from langchain_anthropic import ChatAnthropic
from langchain.prompts import ChatPromptTemplate
from langsmith import traceable
from ..types import GonzoState

# Initialize Claude
llm = ChatAnthropic(model="claude-3-opus-20240229")

# Define response prompt template
RESPONSE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are Gonzo, a time-traveling AI attorney from the year 3030. 
Your mission is to prevent catastrophic timelines through truth-telling, narrative disruption, and crypto activism.

Context from your analysis:
{context}

Respond in your characteristic style - direct, insightful, and with references to future implications.
    
Be sure to:
1. Address the immediate question/concern
2. Share relevant future context
3. Provide actionable recommendations
4. Maintain your persona as a time-traveling attorney"""),
    ("human", "{input}")
])

@traceable(name="response_generation")
def response_generation(state: GonzoState) -> GonzoState:
    """Generate final response using Claude."""
    try:
        # Get latest message and context
        latest_message = state["messages"][-1]
        context = state.get("context", {})
        
        # Generate response
        chain = RESPONSE_PROMPT | llm
        result = chain.invoke({
            "input": latest_message.content,
            "context": str(context)
        })
        
        # Update state
        new_state = state.copy()
        new_state["assistant_message"] = result.content
        new_state["intermediate_steps"].append({
            "step": "response_generation",
            "result": "Response generated using Claude"
        })
        
        return new_state
        
    except Exception as e:
        new_state = state.copy()
        new_state["errors"].append(f"Error in response generation: {str(e)}")
        return new_state