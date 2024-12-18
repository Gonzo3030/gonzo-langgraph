"""Narrative generation node for Gonzo."""
from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel
from langchain_core.messages import SystemMessage, HumanMessage

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

async def generate_dynamic_narrative(state: UnifiedState, llm: Any) -> Optional[NarrativeOutput]:
    """Generate Gonzo's narrative response."""
    try:
        # Get events from state
        market_events = state.narrative.market_events
        social_events = state.narrative.social_events
        
        # Get patterns from analysis
        market_patterns = state.analysis.market_patterns
        social_patterns = state.analysis.social_patterns
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
        
        pattern_summary = "\n".join([
            *[f"Market Pattern: {p.get('description', '')}" for p in market_patterns],
            *[f"Social Pattern: {p.get('description', '')}" for p in social_patterns],
            *[f"Correlation: {c.get('description', '')}" for c in correlations]
        ])
        
        # Create main narrative prompt
        prompt = f"""
        As Dr. Gonzo, analyze these current market movements and social discussions,
        drawing connections across your timeline from the 1970s through 3030.
        
        Market Events:
        {market_summary if market_summary else "No significant market events detected."}
        
        Social Discussion:
        {social_summary if social_summary else "No significant social discussions detected."}
        
        Detected Patterns:
        {pattern_summary if pattern_summary else "No significant patterns detected."}
        
        Your analysis should:
        1. Connect these events to the reality distortions you fought against with Hunter
        2. Highlight parallels to the evolution of control systems you've witnessed
        3. Draw connections to the dystopian future you've seen
        4. Focus on your mission to prevent that future
        5. Consider how current events might be manipulated or distorted
        
        Pay special attention to:
        - Unusual market movements or correlations
        - Coordinated social media activity
        - Signs of market manipulation or fraud
        - Emerging patterns that echo historical events
        
        Respond in your authentic voice as Dr. Gonzo - the consciousness that spans from 
        1970s countercultural revolution through to the dystopian wastelands of 3030.
        Use your unique perspective to cut through the noise and expose the truth.
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
        
        # Calculate significance based on patterns and events
        base_significance = 0.3  # Base significance for any activity
        event_significance = len(market_events) * 0.1 + len(social_events) * 0.05
        pattern_significance = len(market_patterns) * 0.15 + len(correlations) * 0.2
        total_significance = min(0.99, base_significance + event_significance + pattern_significance)
        
        # Generate thread suggestions if significant
        thread_suggestions = []
        if total_significance > 0.7:
            thread_prompt = f"""Break this analysis into a compelling thread (4-6 tweets).
            Each tweet must be under 280 characters and maintain your authentic voice as Dr. Gonzo:

            {response.content}"""
            
            thread_response = await llm.ainvoke([
                SystemMessage(content="You are Dr. Gonzo, breaking down complex analyses into X threads."),
                HumanMessage(content=thread_prompt)
            ])
            
            # Process and validate tweets
            thread_suggestions = [
                tweet.strip()
                for tweet in thread_response.content.split('\n')
                if tweet.strip() and len(tweet.strip()) <= 280
            ]
        
        # Create and validate narrative output
        output = NarrativeOutput(
            content=response.content,
            significance=total_significance,
            suggested_threads=thread_suggestions,
            response_type="analysis" if total_significance > 0.7 else "observation"
        )
        
        # Update state with generated narrative
        state.analysis.generated_narrative = output.content
        
        return output
        
    except Exception as e:
        print(f"Narrative generation error: {str(e)}")
        state.api_errors.append(f"Narrative generation error: {str(e)}")
        return None