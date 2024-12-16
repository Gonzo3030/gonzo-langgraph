from datetime import datetime
from typing import Dict, Any, List
from time import sleep
from langsmith import traceable
from langchain_core.prompts import ChatPromptTemplate
from langchain_anthropic import ChatAnthropic
from ..types import GonzoState
from ..config import ANTHROPIC_MODEL

# Define prompt
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
    ("user", "{input}")
])

def create_thread(text: str, max_length: int = 280) -> List[str]:
    """Break text into tweet-sized chunks while preserving meaning.
    
    Args:
        text: The text to break into tweets
        max_length: Maximum length per tweet (default: 280)
        
    Returns:
        List[str]: List of tweet-sized chunks
    """
    # Account for thread numbering format "🧵 X/Y "
    THREAD_PREFIX_LENGTH = 12  # Length of "🧵 XX/XX " 
    effective_length = max_length - THREAD_PREFIX_LENGTH
    
    # Remove any existing thread numbering and clean text
    clean_text = text.replace('*', '').strip()
    
    # Split into sentences and clean them
    sentences = [s.strip() + "." for s in clean_text.split('.')
                if s.strip()]
    
    tweets = []
    current_tweet = ""
    
    for sentence in sentences:
        # If sentence alone exceeds limit, need to split it
        if len(sentence) > effective_length:
            # If we have accumulated content, add it as a tweet
            if current_tweet:
                tweets.append(current_tweet.strip())
                current_tweet = ""
            
            # Split long sentence into chunks
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
            # Test if adding this sentence would exceed length
            test_tweet = current_tweet + (" " if current_tweet else "") + sentence
            if len(test_tweet) <= effective_length:
                current_tweet = test_tweet
            else:
                if current_tweet:
                    tweets.append(current_tweet.strip())
                current_tweet = sentence
    
    # Add any remaining content
    if current_tweet:
        tweets.append(current_tweet.strip())
    
    # Add thread numbering
    total = len(tweets)
    return [f"🧵 {i+1}/{total} {tweet}" for i, tweet in enumerate(tweets)]

@traceable(name="analyze_narrative")
async def analyze_narrative(state: GonzoState, llm: Any) -> Dict[str, Any]:
    """Generate a raw Gonzo analysis of narrative manipulation.
    
    Args:
        state: Current GonzoState containing message history and context
        llm: Language model for analysis
        
    Returns:
        Dict[str, Any]: Updates to apply to state
    """
    try:
        # Get latest message
        if not state.messages.messages:
            raise ValueError("No messages in state")
            
        latest_msg = state.messages.current_message
        
        # Get the raw Gonzo take
        response = await llm.ainvoke(prompt.format(input=latest_msg))
        gonzo_take = response.content
        print(f"Raw Gonzo Analysis:\n{gonzo_take}")
        
        # Create tweet thread from analysis
        tweet_thread = create_thread(gonzo_take)
        print("\nTweet Thread:")
        for tweet in tweet_thread:
            print(f"\n{tweet}")
        
        # Update state
        state.timestamp = datetime.now()
        state.response.response_content = gonzo_take
        state.response.queued_responses = tweet_thread
        
        # Return updates
        return {
            "response": state.response,
            "timestamp": state.timestamp,
            "next": "respond"
        }
        
    except Exception as e:
        print(f"Narrative analysis error: {str(e)}")
        state.add_error(f"Narrative analysis error: {str(e)}")
        state.timestamp = datetime.now()
        return {
            "memory": state.memory,
            "timestamp": state.timestamp,
            "next": "error"
        }