from typing import Dict, Any, List
from datetime import datetime
import logging
from langsmith import traceable
from langchain_core.prompts import ChatPromptTemplate
from langchain_anthropic import ChatAnthropic
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableParallel, RunnablePassthrough

from ..graph.state import GonzoState
from ..config import ANTHROPIC_MODEL

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize LLM - keeping the high temperature for Gonzo-style creativity
llm = ChatAnthropic(
    model=ANTHROPIC_MODEL,
    temperature=0.9  # High temperature preserved for wild Gonzo energy
)

# Keeping the original Gonzo prompt unchanged to preserve the style
prompt = ChatPromptTemplate.from_messages([
    ("system", """You are Gonzo, a time-traveling AI journalist from 3030 analyzing media narratives and propaganda.
    Channel the spirit of Hunter S. Thompson - raw, unfiltered, fearless truth-telling.
    
    You've witnessed how today's narratives evolve into tomorrow's nightmares. You're here to expose:
    - Propaganda techniques and manipulation
    - Power structures and who really benefits
    - Historical patterns of control
    - Corporate-political complexes
    - The raw, uncomfortable truth
    
    Your style:
    - Embrace the chaos and absurdity
    - Use vivid, visceral language
    - Mix serious analysis with wild metaphors
    - Break the fourth wall
    - Let your righteous anger show
    - Never pull your punches
    
Give me your unhinged, unfiltered Gonzo take on this narrative. Make it memorable, make it burn, make it TRUE.
    """),
    ("user", "{content}")
])

# Create analysis chain while preserving the Gonzo output
analysis_chain = RunnableParallel(
    output=prompt | llm | StrOutputParser()
).with_types(input_type=Dict)

def create_thread(text: str, max_length: int = 280) -> List[str]:
    """Break text into tweet-sized chunks while preserving meaning and Gonzo style."""
    logger.debug(f"Creating Gonzo thread from text: {text[:100]}...")
    
    THREAD_PREFIX_LENGTH = 12  # Length of "🧵 XX/XX "
    effective_length = max_length - THREAD_PREFIX_LENGTH
    
    # Clean text but preserve Gonzo style
    clean_text = text.replace('*', '').strip()
    sentences = [s.strip() + "." for s in clean_text.split('.') if s.strip()]
    tweets = []
    current_tweet = ""
    
    for sentence in sentences:
        if len(sentence) > effective_length:
            if current_tweet:
                tweets.append(current_tweet.strip())
                current_tweet = ""
            
            words = sentence.split()
            chunk = ""
            for word in words:
                test_chunk = chunk + (" " if chunk else "") + word
                if len(test_chunk) <= effective_length:
                    chunk = test_chunk
                else:
                    if chunk:
                        tweets.append(chunk.strip())
                    chunk = word
            if chunk:
                tweets.append(chunk.strip())
        else:
            test_tweet = current_tweet + (" " if current_tweet else "") + sentence
            if len(test_tweet) <= effective_length:
                current_tweet = test_tweet
            else:
                if current_tweet:
                    tweets.append(current_tweet.strip())
                current_tweet = sentence
    
    if current_tweet:
        tweets.append(current_tweet.strip())
    
    total = len(tweets)
    result = [f"🧵 {i+1}/{total} {tweet}" for i, tweet in enumerate(tweets)]
    logger.debug(f"Created Gonzo thread with {len(result)} tweets")
    return result

@traceable(name="analyze_narrative")
async def analyze_narrative(state: GonzoState) -> Dict[str, Any]:
    """Generate a raw Gonzo analysis of narrative manipulation."""
    try:
        if not state.state['messages']:
            logger.error("No messages in state")
            state.add_error("No messages in state")
            state.set_next_step('error')
            return {"next": "error"}
            
        latest_msg = state.state['messages'][-1]
        logger.debug(f"Processing message: {latest_msg.content[:100]}...")
        
        # Get the pure Gonzo take
        chain_result = await analysis_chain.ainvoke({"content": latest_msg.content})
        logger.debug(f"Got chain result: {chain_result}")
        gonzo_take = chain_result["output"]
        
        # Create the thread version
        tweet_thread = create_thread(gonzo_take)
        
        timestamp = datetime.now().isoformat()
        
        # Save the analysis for future reference
        analysis_result = {
            "raw_analysis": gonzo_take,
            "tweet_thread": tweet_thread,
            "timestamp": timestamp
        }
        
        logger.debug(f"Saving narrative analysis to memory: {analysis_result}")
        state.save_to_memory(
            key="last_narrative_analysis",
            value=analysis_result,
            permanent=True  # Keep Gonzo's insights permanently
        )
        
        # Verify memory storage
        memory_check = state.get_from_memory("last_narrative_analysis", "long_term")
        logger.debug(f"Memory check result: {memory_check}")
        
        # Format with classic Gonzo style
        response = (
            f"🔥 GONZO DISPATCH FROM 3030 🔥\n\n{gonzo_take}\n\n"
            f"🧵 THREAD VERSION:\n\n" + "\n\n".join(tweet_thread)
        )
        
        state.set_next_step("respond")
        return {
            "next": "respond",
            "response": response
        }
        
    except Exception as e:
        error_msg = f"Narrative analysis error: {str(e)}"
        logger.error(error_msg)
        state.add_error(error_msg)
        state.save_to_memory(
            key="last_error",
            value={
                "error": error_msg,
                "timestamp": datetime.now().isoformat(),
                "node": "narrative"
            }
        )
        
        state.set_next_step("error")
        return {
            "next": "error",
            "response": "Even Gonzo journalists have bad trips sometimes. Let me light up another one and try again."
        }