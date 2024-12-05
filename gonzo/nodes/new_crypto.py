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

# Initialize LLM
llm = ChatAnthropic(
    model=ANTHROPIC_MODEL,
    temperature=0.85
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
    ("user", "{content}")
])

# Create analysis chain
analysis_chain = RunnableParallel(
    output=prompt | llm | StrOutputParser()
).with_types(input_type=Dict)

def create_crypto_report(analysis: str) -> Dict[str, str]:
    """Structure the crypto analysis into a detailed report format."""
    logger.debug(f"Creating crypto report from analysis: {analysis[:100]}...")
    sections = {
        "🏦 MARKET ANALYSIS": "",
        "📊 TECHNICAL INDICATORS": "",
        "🌊 SOCIAL SENTIMENT": "",
        "⚖️ REGULATORY LANDSCAPE": "",
        "🔮 FUTURE IMPLICATIONS": ""
    }
    
    current_section = ""
    current_content = []
    
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
    
    result = {k: v for k, v in sections.items() if v}
    logger.debug(f"Created report with {len(result)} sections")
    return result

def create_thread(text: str, max_length: int = 280) -> List[str]:
    """Break text into tweet-sized chunks while preserving meaning."""
    logger.debug(f"Creating thread from text: {text[:100]}...")
    THREAD_PREFIX_LENGTH = 12
    effective_length = max_length - THREAD_PREFIX_LENGTH
    
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
    result = [f"💰 {i+1}/{total} {tweet}" for i, tweet in enumerate(tweets)]
    logger.debug(f"Created thread with {len(result)} tweets")
    return result

@traceable(name="analyze_crypto")
async def analyze_crypto(state: GonzoState) -> Dict[str, Any]:
    """Generate a detailed Gonzo analysis of crypto markets and trends."""
    try:
        if not state.state['messages']:
            logger.error("No messages in state")
            state.add_error("No messages in state")
            state.set_next_step('error')
            return {"next": "error"}
            
        latest_msg = state.state['messages'][-1]
        logger.debug(f"Processing message: {latest_msg.content[:100]}...")
        
        # Get analysis using chain
        chain_result = await analysis_chain.ainvoke({"content": latest_msg.content})
        logger.debug(f"Got chain result: {chain_result}")
        gonzo_take = chain_result["output"]
        
        # Create structured report and thread
        crypto_report = create_crypto_report(gonzo_take)
        tweet_thread = create_thread(gonzo_take)
        
        timestamp = datetime.now().isoformat()
        
        # Save results to memory
        analysis_result = {
            "raw_analysis": gonzo_take,
            "structured_report": crypto_report,
            "tweet_thread": tweet_thread,
            "timestamp": timestamp
        }
        
        logger.debug(f"Saving analysis result to memory: {analysis_result}")
        state.save_to_memory(
            key="last_crypto_analysis",
            value=analysis_result,
            permanent=True  # Save crypto analysis permanently
        )
        
        # Verify memory storage
        memory_check = state.get_from_memory("last_crypto_analysis", "long_term")
        logger.debug(f"Memory check result: {memory_check}")
        
        # Format final response
        response = (
            f"💰 GONZO CRYPTO DISPATCH FROM 3030 💰\n\n{gonzo_take}\n\n"
            f"📊 STRUCTURED ANALYSIS:\n\n" +
            '\n\n'.join(f"{k}:\n{v}" for k, v in crypto_report.items()) +
            f"\n\n🧵 THREAD VERSION:\n\n" + "\n\n".join(tweet_thread)
        )
        
        state.set_next_step("respond")
        return {
            "next": "respond",
            "response": response
        }
        
    except Exception as e:
        error_msg = f"Crypto analysis error: {str(e)}"
        logger.error(error_msg)
        state.add_error(error_msg)
        state.save_to_memory(
            key="last_error",
            value={
                "error": error_msg,
                "timestamp": datetime.now().isoformat(),
                "node": "crypto"
            }
        )
        
        state.set_next_step("error")
        return {
            "next": "error",
            "response": "The crypto markets are as volatile as my connection to this timeline. Let me realign my neural networks and try again."
        }