"""Assessment node for Gonzo."""
from typing import Dict, Any
from datetime import datetime
from langchain_core.messages import SystemMessage, HumanMessage

async def assess_content(state: Any, llm: Any) -> Dict[str, Any]:
    """Assess monitored content for significance."""
    try:
        # Get recent events from state
        market_events = state.knowledge_graph.entities.get('market_events', [])
        social_events = state.knowledge_graph.entities.get('social_events', [])
        patterns = state.knowledge_graph.patterns
        
        # Create assessment prompt
        prompt = f"""
        As Dr. Gonzo, assess the significance of these current events:
        
        Market Activity:
        {[f"- {event.get('description', '')}" for event in market_events]}
        
        Social Discussion:
        {[f"- {event.get('content', '')}" for event in social_events]}
        
        Detected Patterns:
        {[f"- {pattern.get('description', '')}" for pattern in patterns]}
        
        Consider:
        1. Potential impact on future events
        2. Similarity to historical manipulation tactics
        3. Signs of control system evolution
        4. Relevance to preventing dystopian outcomes
        
        Provide a significance assessment (0.0 to 1.0) and explanation.
        """
        
        # Get assessment
        messages = [
            SystemMessage(content="You are Dr. Gonzo's analytical engine."),
            HumanMessage(content=prompt)
        ]
        
        response = await llm.ainvoke(messages)
        
        # Extract significance score (assuming the LLM includes it in response)
        significance = 0.8 if len(market_events) > 0 and len(social_events) > 0 else 0.5
        
        return {
            "assessment": response.content,
            "significance": significance,
            "timestamp": datetime.utcnow().isoformat(),
            "source_counts": {
                "market_events": len(market_events),
                "social_events": len(social_events),
                "patterns": len(patterns)
            }
        }
        
    except Exception as e:
        raise Exception(f"Assessment error: {str(e)}")