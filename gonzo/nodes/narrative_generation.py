"""Narrative generation node for Gonzo."""
from typing import Dict, Any
from datetime import datetime
from langchain_core.messages import SystemMessage, HumanMessage

async def generate_dynamic_narrative(state: Any, llm: Any) -> Dict[str, Any]:
    """Generate Gonzo's narrative response."""
    try:
        # Get context from state
        context = state.narrative.context
        market_events = context.get('market_events', [])
        social_events = context.get('social_events', [])
        patterns = context.get('patterns', [])
        
        # Create prompts for different narrative parts
        market_summary = "\n".join(
            f"- {event.get('symbol', 'Unknown')}: {event.get('description', '')}" 
            for event in market_events
        )
        
        social_summary = "\n".join(
            f"- {event.get('content', '')}" 
            for event in social_events
        )
        
        pattern_summary = "\n".join(
            f"- {pattern.get('description', '')}" 
            for pattern in patterns
        )
        
        # Create main narrative prompt
        prompt = f"""
        As Dr. Gonzo, analyze these current market movements and social discussions,
        drawing connections across your timeline from the 1970s through 3030.
        
        Market Events:
        {market_summary}
        
        Social Discussion:
        {social_summary}
        
        Detected Patterns:
        {pattern_summary}
        
        Connect these events to:
        1. The reality distortions you fought with Hunter
        2. The evolution of control systems you've witnessed
        3. The dystopian future you've seen
        4. Your mission to prevent that future
        
        Respond in your authentic voice, weaving these threads into a cohesive narrative.
        """
        
        # Generate narrative
        messages = [
            SystemMessage(content="You are Dr. Gonzo's consciousness across time - from the 1970s through 3030."),
            HumanMessage(content=prompt)
        ]
        
        response = await llm.ainvoke(messages)
        
        # Generate thread suggestions if significant
        thread_suggestions = []
        if state.analysis.significance > 0.7:
            thread_prompt = f"Break this analysis into a compelling thread (4-6 tweets):\n\n{response.content}"
            thread_response = await llm.ainvoke([
                SystemMessage(content="You are Dr. Gonzo, breaking down complex analyses into X threads."),
                HumanMessage(content=thread_prompt)
            ])
            
            thread_suggestions = [
                tweet.strip()
                for tweet in thread_response.content.split('\n')
                if tweet.strip() and len(tweet.strip()) <= 280
            ]
        
        return {
            "content": response.content,
            "significance": state.analysis.significance,
            "suggested_threads": thread_suggestions,
            "response_type": "analysis" if state.analysis.significance > 0.7 else "observation"
        }
        
    except Exception as e:
        raise Exception(f"Narrative generation error: {str(e)}")