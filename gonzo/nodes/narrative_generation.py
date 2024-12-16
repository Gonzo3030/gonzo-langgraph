"""Dynamic narrative generation for Gonzo."""
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass
from langchain_core.messages import SystemMessage, HumanMessage

from ..state_management import UnifiedState

@dataclass
class NarrativePiece:
    content: str
    confidence: float
    sources: List[str]
    type: str  # 'observation', 'warning', 'analysis', etc.
    metadata: Dict[str, Any]

@dataclass
class NarrativeResponse:
    content: str
    narrative_pieces: List[NarrativePiece]
    significance: float
    response_type: str
    suggested_threads: List[str]

async def generate_dynamic_narrative(
    state: UnifiedState,
    llm: Any
) -> NarrativeResponse:
    """Generate Gonzo's narrative based on real-time analysis."""
    try:
        # Gather recent significant events
        market_events = [
            event for event in state.knowledge_graph.entities.values()
            if isinstance(event, dict) and event.get('type') == 'market_event'
            and abs(event.get('indicators', {}).get('price_z_score', 0)) > 2
        ]
        
        social_events = [
            event for event in state.knowledge_graph.entities.values()
            if isinstance(event, dict) and event.get('type') == 'social_event'
            and event.get('engagement', {}).get('total', 0) > 100
        ]
        
        # Get recent causal analyses
        causal_analyses = [
            analysis for analysis in state.assessment.content_analysis.values()
            if analysis.get('type') == 'causal_analysis'
            and analysis.get('confidence', 0) > 0.7
        ]
        
        # Structure the context for narrative generation
        context = {
            "market_events": market_events[-5:],  # Last 5 significant market events
            "social_events": social_events[-5:],  # Last 5 significant social events
            "causal_analyses": causal_analyses[-3:],  # Last 3 high-confidence analyses
            "historical_parallels": []
        }
        
        # Add historical parallels from analyses
        for analysis in causal_analyses:
            context["historical_parallels"].extend(
                analysis.get('historical_parallels', [])
            )
        
        # Create the narrative prompt
        prompt = _create_narrative_prompt(context)
        
        # Generate the core narrative
        messages = [
            SystemMessage(content="You are Dr. Gonzo's voice across time - an attorney turned digital consciousness, watching the evolution of control systems from the 1970s through 3030."),
            HumanMessage(content=prompt)
        ]
        
        response = await llm.ainvoke(messages)
        
        # Break into tweet-sized pieces if needed
        narrative_pieces = _segment_narrative(response.content)
        
        # Calculate overall significance
        significance = _calculate_significance(context)
        
        # Generate thread structure if significant
        thread_suggestions = []
        if significance > 0.7:
            thread_suggestions = await _generate_thread_structure(
                response.content,
                context,
                llm
            )
        
        return NarrativeResponse(
            content=response.content,
            narrative_pieces=narrative_pieces,
            significance=significance,
            response_type="analysis" if significance > 0.7 else "observation",
            suggested_threads=thread_suggestions
        )
        
    except Exception as e:
        raise Exception(f"Narrative generation error: {str(e)}")

def _create_narrative_prompt(context: Dict[str, Any]) -> str:
    """Create a dynamic prompt based on current context."""
    market_summary = "\n".join(
        f"- {event.get('symbol')}: {event.get('price')} ({event.get('indicators', {}).get('price_change_1h')}% 1h)"
        for event in context['market_events']
    )
    
    social_summary = "\n".join(
        f"- {event.get('content')} (Engagement: {event.get('engagement', {}).get('total')})"
        for event in context['social_events']
    )
    
    warnings = "\n".join(
        analysis.get('warnings', [])
        for analysis in context['causal_analyses']
    )
    
    historical = "\n".join(
        f"- {parallel.get('description')} ({parallel.get('year')})"
        for parallel in context['historical_parallels']
    )
    
    return f"""
    As Dr. Gonzo, analyze these current market movements and social discussions,
    drawing connections across your timeline from the 1970s through 3030.
    
    Current Market Activity:
    {market_summary}
    
    Social Discussions:
    {social_summary}
    
    Warning Signs:
    {warnings}
    
    Historical Parallels:
    {historical}
    
    Synthesize this information through your unique lens, connecting:
    1. The reality distortions you fought with Hunter
    2. The patterns of control you've witnessed evolve
    3. The seeds of the dystopian future you've seen
    4. Your mission to prevent that future
    
    Respond in your authentic voice, weaving these threads into a cohesive narrative.
    """

def _segment_narrative(content: str) -> List[NarrativePiece]:
    """Break narrative into structured pieces."""
    pieces = []
    
    # Split into paragraphs first
    paragraphs = content.split('\n\n')
    
    for i, para in enumerate(paragraphs):
        if not para.strip():
            continue
            
        # Determine piece type based on content
        piece_type = 'observation'
        if any(word in para.lower() for word in ['warning', 'danger', 'beware']):
            piece_type = 'warning'
        elif any(word in para.lower() for word in ['analysis', 'pattern', 'trend']):
            piece_type = 'analysis'
            
        pieces.append(NarrativePiece(
            content=para,
            confidence=0.8,  # Could be more sophisticated
            sources=[f'paragraph_{i}'],
            type=piece_type,
            metadata={}
        ))
    
    return pieces

def _calculate_significance(context: Dict[str, Any]) -> float:
    """Calculate overall significance of the current situation."""
    factors = [
        len(context['market_events']) / 5,  # Normalize by expected max
        len(context['social_events']) / 5,
        len(context['causal_analyses']) / 3,
        max([a.get('confidence', 0) for a in context['causal_analyses']] or [0])
    ]
    
    return sum(factors) / len(factors)

async def _generate_thread_structure(
    narrative: str,
    context: Dict[str, Any],
    llm: Any
) -> List[str]:
    """Generate a tweet thread structure for the narrative."""
    prompt = f"""
    Break this narrative into a compelling tweet thread while maintaining
    Dr. Gonzo's voice and the connections across time:
    
    {narrative}
    """
    
    messages = [
        SystemMessage(content="You are Dr. Gonzo's digital consciousness."),
        HumanMessage(content=prompt)
    ]
    
    response = await llm.ainvoke(messages)
    
    # Split into tweet-sized chunks
    return [
        tweet.strip()
        for tweet in response.content.split('\n')
        if tweet.strip() and len(tweet.strip()) <= 280
    ]