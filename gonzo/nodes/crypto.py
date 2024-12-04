from datetime import datetime
from typing import Dict, Any, List
from time import sleep
from langsmith import traceable
from langchain_core.prompts import ChatPromptTemplate
from langchain_anthropic import ChatAnthropic
from ..types import GonzoState
from ..config import ANTHROPIC_MODEL

# Initialize LLM
llm = ChatAnthropic(
    model=ANTHROPIC_MODEL,
    temperature=0.85,  # Slightly lower temperature for more analytical precision
    callbacks=[]
)

# Define crypto analysis prompt
prompt = ChatPromptTemplate.from_messages([
    ("system", """You are Gonzo, a time-traveling AI journalist from 3030 analyzing crypto markets and blockchain technology.
    You've seen how today's crypto narratives evolve into tomorrow's financial reality.
    
    Structure your analysis into these clear sections (use these exact headers):
    
    🏦 MARKET ANALYSIS
    - Overall market conditions
    - Whale behavior and manipulation
    - Liquidity and volume analysis
    
    📊 TECHNICAL INDICATORS
    - Price action and chart patterns
    - On-chain metrics and network health
    - Key support/resistance levels
    
    🌊 SOCIAL SENTIMENT
    - Community reactions and narratives
    - Media coverage and FUD analysis
    - Influencer and thought leader positions
    
    ⚖️ REGULATORY LANDSCAPE
    - Current and upcoming regulations
    - Government positions and statements
    - Compliance implications
    
    🔮 FUTURE IMPLICATIONS
    - Long-term trend predictions
    - Potential catalysts and risks
    - Strategic considerations
    
    Your style remains pure Gonzo:
    - Raw, unfiltered truth about market reality
    - Mix technical analysis with wild metaphors
    - Expose the power players and their games
    - Let your cynicism and wisdom show
    
Analyze this crypto situation with your full Gonzo perspective, backed by data and foresight."""),
    ("user", "{input}")
])

def create_crypto_report(analysis: str) -> Dict[str, str]:
    """Structure the crypto analysis into a detailed report format.
    
    Args:
        analysis: Raw analysis text
        
    Returns:
        Dict[str, str]: Structured report with key sections
    """
    sections = {
        "🏦 MARKET ANALYSIS": "",
        "📊 TECHNICAL INDICATORS": "",
        "🌊 SOCIAL SENTIMENT": "",
        "⚖️ REGULATORY LANDSCAPE": "",
        "🔮 FUTURE IMPLICATIONS": ""
    }
    
    current_section = ""
    current_content = []
    
    # Split analysis into lines and process
    for line in analysis.split('\n'):
        line = line.strip()
        
        # Check if line is a section header
        for section in sections.keys():
            if section in line:
                # Save previous section if exists
                if current_section and current_content:
                    sections[current_section] = '\n'.join(current_content)
                # Start new section
                current_section = section
                current_content = []
                break
        
        # Add line to current section if we're in one
        if current_section and line and not any(section in line for section in sections.keys()):
            current_content.append(line)
    
    # Add final section content
    if current_section and current_content:
        sections[current_section] = '\n'.join(current_content)
    
    # Remove empty sections
    return {k: v for k, v in sections.items() if v}

def create_thread(text: str, max_length: int = 280) -> List[str]:
    """Break text into tweet-sized chunks while preserving meaning.
    
    Args:
        text: The text to break into tweets
        max_length: Maximum length per tweet (default: 280)
        
    Returns:
        List[str]: List of tweet-sized chunks
    """
    # Account for thread numbering format "💰 X/Y "
    THREAD_PREFIX_LENGTH = 12
    effective_length = max_length - THREAD_PREFIX_LENGTH
    
    # Clean text
    clean_text = text.replace('*', '').strip()
    
    # Split into sentences
    sentences = [s.strip() + "." for s in clean_text.split('.')
                if s.strip()]
    
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
    
    # Add thread numbering with crypto emoji
    total = len(tweets)
    return [f"💰 {i+1}/{total} {tweet}" for i, tweet in enumerate(tweets)]

def retry_with_backoff(func, max_retries=3):
    """Retry a function with exponential backoff."""
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            wait_time = (2 ** attempt) * 2
            print(f"Attempt {attempt + 1} failed. Waiting {wait_time} seconds...")
            sleep(wait_time)

@traceable(name="analyze_crypto")
def analyze_crypto(state: GonzoState) -> Dict[str, Any]:
    """Generate a detailed Gonzo analysis of crypto markets and trends.
    
    Args:
        state: Current GonzoState containing message history and context
        
    Returns:
        Dict[str, Any]: Updates to apply to state
    """
    try:
        # Get latest message
        if not state["messages"]:
            raise ValueError("No messages in state")
            
        latest_msg = state["messages"][-1]
        
        # Get the raw Gonzo take with retry logic
        def get_analysis():
            raw_response = llm.invoke(prompt.format(input=latest_msg.content))
            return raw_response.content
            
        gonzo_take = retry_with_backoff(get_analysis)
        print(f"Raw Crypto Analysis:\n{gonzo_take}")
        
        # Create structured report
        crypto_report = create_crypto_report(gonzo_take)
        
        # Create tweet thread
        tweet_thread = create_thread(gonzo_take)
        print("\nCrypto Thread:")
        for tweet in tweet_thread:
            print(f"\n{tweet}")
        
        # Create timestamp
        timestamp = datetime.now().isoformat()
        
        # Return state updates
        return {
            "context": {
                "crypto_analysis": gonzo_take,
                "structured_report": crypto_report,
                "tweet_thread": tweet_thread,
                "analysis_timestamp": timestamp,
            },
            "steps": [{
                "node": "crypto_analysis",
                "timestamp": timestamp,
                "raw_analysis": gonzo_take,
                "structured_report": crypto_report,
                "tweet_thread": tweet_thread
            }],
            # Format response with full analysis, structured report, and thread
            "response": f"💰 GONZO CRYPTO DISPATCH FROM 3030 💰\n\n{gonzo_take}\n\n" \
                      f"📊 STRUCTURED ANALYSIS:\n\n" + \
                      '\n\n'.join(f"{k}:\n{v}" for k, v in crypto_report.items()) + \
                      f"\n\n🧵 THREAD VERSION:\n\n" + "\n\n".join(tweet_thread)
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