from datetime import datetime
from typing import Dict, Any, List, Callable
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

def retry_with_backoff(func: Callable, max_retries: int = 3) -> Any:
    """Retry a function with exponential backoff."""
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:  # Last attempt
                raise e
            wait_time = (2 ** attempt) * 2  # 2, 4, 8 seconds
            print(f"Attempt {attempt + 1} failed. Waiting {wait_time} seconds...")
            sleep(wait_time)

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
    """Break text into tweet-sized chunks while preserving meaning."""
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

def format_response(analysis: str, report: Dict[str, str], thread: List[str], memories: Dict[str, List[TimelineMemory]]) -> str:
    """Format the full response including analysis, report, and thread."""
    memories_used = "\n".join([
        f"Timeline: {timeline}\n" + "\n".join([f"- {m.content}" for m in mems])
        for timeline, mems in memories.items()
    ])
    
    return (
        f"💰 GONZO CRYPTO DISPATCH FROM 3030 💰\n\n"
        f"Drawing from my memories...\n\n{memories_used}\n\n"
        f"{analysis}\n\n"
        f"📊 STRUCTURED ANALYSIS:\n\n" + 
        '\n\n'.join(f"{k}:\n{v}" for k, v in report.items()) + 
        f"\n\n🧵 THREAD VERSION:\n\n" + "\n\n".join(thread)
    )

@traceable(name="analyze_crypto_with_memory")
async def analyze_crypto_with_memory(
    state: GonzoState,
    memory_interface: MemoryInterface
) -> Dict[str, Any]:
    """Generate a detailed Gonzo analysis of crypto markets and trends, enhanced with memories."""
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