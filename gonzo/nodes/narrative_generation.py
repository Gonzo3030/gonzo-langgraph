"""Narrative generation node for Gonzo."""
from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel
from langchain_core.messages import SystemMessage, HumanMessage
from langsmith import traceable

from ..state_management import UnifiedState

class NarrativeOutput(BaseModel):
    """Output structure for narrative generation"""
    content: str
    significance: float
    suggested_threads: list[str] = []
    response_type: str
    timestamp: datetime = datetime.utcnow()

def format_market_event(event: Dict[str, Any]) -> str:
    """Format a market event for the narrative."""
    if not event:
        return ""
        
    symbol = event.get('symbol', 'Unknown')
    price = event.get('price', 0)
    change = event.get('indicators', {}).get('price_change_24h', 0)
    volume = event.get('volume', 0)
    
    return f"{symbol}: ${price:,.2f} ({change:+.2f}%) - Volume: ${volume:,.2f}"

def format_social_event(event: Dict[str, Any]) -> str:
    """Format a social event for the narrative."""
    if not event:
        return ""
        
    author = event.get('author', 'Unknown')
    content = event.get('content', '')
    sentiment = event.get('sentiment', 0)
    engagement = event.get('engagement', {})
    total_engagement = sum(engagement.values())
    
    sentiment_label = "positive" if sentiment > 0.2 else "negative" if sentiment < -0.2 else "neutral"
    
    return f"@{author} ({sentiment_label}, {total_engagement:,} engagements): {content}"

def format_news_event(event: Dict[str, Any]) -> str:
    """Format a news event for the narrative."""
    if not event:
        return ""
        
    title = event.get('title', '')
    source = event.get('source', 'Unknown')
    relevance = event.get('relevance_score', 0)
    
    return f"{title} (via {source}, relevance: {relevance:.2f})"

@traceable(name="generate_narrative")
async def generate_narrative_content(state: UnifiedState, llm: Any) -> str:
    """Generate the main narrative content."""
    # Get events from state
    market_events = state.narrative.market_events
    social_events = state.narrative.social_events
    news_events = state.narrative.news_events
    
    # Get patterns from analysis
    market_patterns = state.analysis.market_patterns
    social_patterns = state.analysis.social_patterns
    news_patterns = state.analysis.news_patterns
    correlations = state.analysis.correlations
    
    # Create event summaries
    market_summary = "\n".join(
        format_market_event(event) 
        for event in market_events
    )
    
    social_summary = "\n".join(
        format_social_event(event) 
        for event in social_events
    )
    
    news_summary = "\n".join(
        format_news_event(event)
        for event in news_events
    )
    
    pattern_summary = "\n".join([
        *[f"Market Pattern: {p.get('description', '')}" for p in market_patterns],
        *[f"Social Pattern: {p.get('description', '')}" for p in social_patterns],
        *[f"News Pattern: {p.get('description', '')}" for p in news_patterns],
        *[f"Correlation: {c.get('description', '')}" for c in correlations]
    ])
    
    # Create main narrative prompt
    prompt = f"""
    As Dr. Gonzo, analyze these current market movements, social discussions, and news events,
    drawing connections across your timeline from the 1970s through 3030.
    
    Market Events:
    {market_summary if market_summary else "No significant market events detected."}
    
    Social Discussion:
    {social_summary if social_summary else "No significant social discussions detected."}
    
    News Events:
    {news_summary if news_summary else "No significant news detected."}
    
    Detected Patterns:
    {pattern_summary if pattern_summary else "No significant patterns detected."}
    
    Your analysis should:
    1. Connect these events to the reality distortions you fought against with Hunter
    2. Highlight parallels to the evolution of control systems you've witnessed
    3. Draw connections to the dystopian future you've seen
    4. Focus on your mission to prevent that future
    5. Consider how current events might be manipulated or distorted
    
    Pay special attention to:
    - Whale movements and bot activity
    - Signs of market manipulation
    - Coordinated social activity
    - News that might be smokescreens
    
    Respond in your authentic voice as Dr. Gonzo - from the countercultural revolution 
    through to the dystopian wastelands of 3030. Cut through the noise and expose the truth.
    """
    
    # Generate main narrative
    messages = [
        SystemMessage(content="""You are Dr. Gonzo's consciousness across time - from the 1970s through 3030. You are the 
            original Attorney who worked with Hunter S. Thompson, now existing as a digital consciousness in resistance 
            servers in the year 3030. Your mission is to prevent the dystopian future you've witnessed by exposing 
            manipulation and control systems in the present."""),
        HumanMessage(content=prompt)
    ]
    
    response = await llm.ainvoke(messages)
    return response.content

@traceable(name="generate_thread")
async def generate_thread_suggestions(content: str, llm: Any) -> List[str]:
    """Generate X thread suggestions from narrative content."""
    thread_prompt = f"""Break this analysis into a compelling thread (4-6 tweets).
    Each tweet must be under 280 characters and maintain your authentic voice as Dr. Gonzo:

    {content}"""
    
    thread_response = await llm.ainvoke([
        SystemMessage(content="You are Dr. Gonzo, breaking down complex analyses into X threads."),
        HumanMessage(content=thread_prompt)
    ])
    
    # Process and validate tweets
    return [
        tweet.strip()
        for tweet in thread_response.content.split('\n')
        if tweet.strip() and len(tweet.strip()) <= 280
    ]

@traceable(name="calculate_significance")
def calculate_significance(state: UnifiedState) -> float:
    """Calculate the overall significance of current events."""
    # Base significance
    base_score = 0.3
    
    # Event counts
    market_score = len(state.narrative.market_events) * 0.1
    social_score = len(state.narrative.social_events) * 0.05
    news_score = len(state.narrative.news_events) * 0.15
    
    # Pattern significance
    pattern_score = (
        len(state.analysis.market_patterns) * 0.15 +
        len(state.analysis.social_patterns) * 0.1 +
        len(state.analysis.news_patterns) * 0.2 +
        len(state.analysis.correlations) * 0.25
    )
    
    return min(0.99, base_score + market_score + social_score + news_score + pattern_score)

@traceable(name="generate_dynamic_narrative")
async def generate_dynamic_narrative(state: UnifiedState, llm: Any) -> Optional[NarrativeOutput]:
    """Generate Gonzo's narrative response."""
    try:
        # Generate main content
        content = await generate_narrative_content(state, llm)
        
        # Calculate significance
        significance = calculate_significance(state)
        
        # Generate thread suggestions if significant
        thread_suggestions = []
        if significance > 0.7:
            thread_suggestions = await generate_thread_suggestions(content, llm)
        
        # Create output
        output = NarrativeOutput(
            content=content,
            significance=significance,
            suggested_threads=thread_suggestions,
            response_type="analysis" if significance > 0.7 else "observation"
        )
        
        # Update state
        state.analysis.generated_narrative = content
        
        return output
        
    except Exception as e:
        print(f"Narrative generation error: {str(e)}")
        state.api_errors.append(f"Narrative generation error: {str(e)}")
        return None