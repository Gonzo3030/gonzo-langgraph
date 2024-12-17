"""Pattern detection node for Gonzo."""
from typing import Dict, Any, List
from datetime import datetime
from langchain_core.messages import SystemMessage, HumanMessage

async def detect_patterns(state: Any, llm: Any) -> Dict[str, Any]:
    """Detect patterns in market and social data."""
    try:
        market_events = state.knowledge_graph.entities.get('market_events', [])
        social_events = state.knowledge_graph.entities.get('social_events', [])
        
        # Create pattern detection prompt
        prompt = f"""
        As Dr. Gonzo, analyze these events for patterns of manipulation and control:
        
        Market Events:
        {[f"- {event.get('description', '')}" for event in market_events]}
        
        Social Activity:
        {[f"- {event.get('content', '')}" for event in social_events]}
        
        Look for:
        1. Signs of market manipulation similar to what you've seen across time
        2. Social engineering tactics that echo through history
        3. Control systems evolving from analog to digital
        4. Seeds of the dystopian future you've witnessed
        
        Identify and describe any significant patterns.
        """
        
        # Get pattern analysis
        messages = [
            SystemMessage(content="You are Dr. Gonzo's pattern recognition system."),
            HumanMessage(content=prompt)
        ]
        
        response = await llm.ainvoke(messages)
        
        # Extract and structure patterns
        patterns = [
            {
                "description": response.content,
                "timestamp": datetime.utcnow().isoformat(),
                "source_events": {
                    "market": len(market_events),
                    "social": len(social_events)
                },
                "significance": 0.8 if len(market_events) > 0 and len(social_events) > 0 else 0.5
            }
        ]
        
        return {
            "patterns": patterns,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise Exception(f"Pattern detection error: {str(e)}")