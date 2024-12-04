from datetime import datetime
from typing import Dict, Any, List
from time import sleep
from langsmith import traceable
from langchain_anthropic import ChatAnthropic
from ..types import GonzoState
from ..config import ANTHROPIC_MODEL
from ..memory.interfaces import MemoryInterface, TimelineMemory
from .prompts.crypto_prompt import create_crypto_prompt

# Initialize LLM
llm = ChatAnthropic(
    model=ANTHROPIC_MODEL,
    temperature=0.85,
    callbacks=[]
)

@traceable(name="analyze_crypto_with_memory")
async def analyze_crypto_with_memory(
    state: GonzoState,
    memory_interface: MemoryInterface
) -> Dict[str, Any]:
    """Generate a detailed Gonzo analysis of crypto markets and trends, enhanced with memories.
    
    Args:
        state: Current GonzoState containing message history and context
        memory_interface: Interface to access Gonzo's memories
        
    Returns:
        Dict[str, Any]: Updates to apply to state
    """
    try:
        # Get latest message
        if not state["messages"]:
            raise ValueError("No messages in state")
            
        latest_msg = state["messages"][-1]
        
        # Get relevant memories
        memories = {
            "pre_1974": await memory_interface.get_relevant_memories(
                query=latest_msg.content,
                category="crypto",
                timeline="pre_1974"
            ),
            "dark_period": await memory_interface.get_relevant_memories(
                query=latest_msg.content,
                category="crypto",
                timeline="dark_period"
            ),
            "future": await memory_interface.get_relevant_memories(
                query=latest_msg.content,
                category="crypto",
                timeline="future"
            )
        }
        
        # Create memory-enhanced prompt
        prompt = create_crypto_prompt(memories)
        
        # Get the raw Gonzo take with retry logic
        def get_analysis():
            raw_response = llm.invoke(prompt.format(input=latest_msg.content))
            return raw_response.content
            
        gonzo_take = retry_with_backoff(get_analysis)
        print(f"Raw Crypto Analysis:\n{gonzo_take}")
        
        # Create structured report
        crypto_report = create_crypto_report(gonzo_take)
        
        # Store new insights as memories
        new_memory = TimelineMemory(
            content=gonzo_take,
            timestamp=datetime.now(),
            category="crypto",
            metadata={
                "report": crypto_report,
                "query": latest_msg.content
            }
        )
        await memory_interface.store_memory(new_memory)
        
        # Create tweet thread
        tweet_thread = create_thread(gonzo_take)
        
        timestamp = datetime.now().isoformat()
        
        return {
            "context": {
                "crypto_analysis": gonzo_take,
                "structured_report": crypto_report,
                "tweet_thread": tweet_thread,
                "analysis_timestamp": timestamp,
                "relevant_memories": memories
            },
            "steps": [{
                "node": "crypto_analysis",
                "timestamp": timestamp,
                "raw_analysis": gonzo_take,
                "structured_report": crypto_report,
                "tweet_thread": tweet_thread,
                "memories_used": {
                    timeline: len(mems) for timeline, mems in memories.items()
                }
            }],
            "response": format_response(
                analysis=gonzo_take,
                report=crypto_report,
                thread=tweet_thread,
                memories=memories
            )
        }
        
    except Exception as e:
        print(f"Crypto analysis error: {str(e)}")
        timestamp = datetime.now().isoformat()
        return {
            "context": {
                "crypto_error": str(e),
                "analysis_timestamp": timestamp
            },
            "steps": [{
                "node": "crypto_analysis",
                "error": str(e),
                "timestamp": timestamp
            }],
            "response": "The crypto markets are as volatile as my connection to this timeline. Let me realign my neural networks and try again."
        }