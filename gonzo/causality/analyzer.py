from typing import List, Dict, Any, Optional
from datetime import datetime
from langsmith import traceable
from langchain_core.messages import SystemMessage, HumanMessage
from .types import (
    CausalEvent,
    TimelineChain,
    CausalAnalysis,
    EventCategory,
    EventScope
)

class CausalAnalyzer:
    """Analyzes current events against known causal chains."""
    
    def __init__(self, llm: Any):
        self.event_chains: Dict[str, TimelineChain] = {}
        self.events: Dict[str, CausalEvent] = {}
        self.llm = llm
        
    def add_chain(self, chain: TimelineChain) -> None:
        """Add a causal chain to the analyzer."""
        self.event_chains[chain.id] = chain
        for event in chain.events:
            self.events[event.id] = event
    
    @traceable(name="analyze_current_event")
    async def analyze_current_event(
        self,
        event_description: str,
        category: EventCategory,
        scope: EventScope,
        current_date: datetime,
        metadata: Optional[Dict] = None
    ) -> CausalAnalysis:
        """Analyze a current event against known causal chains."""
        
        # Use LLM to find historical parallels
        parallels_prompt = f"""
        As Dr. Gonzo, analyze this current event and identify historical parallels from pre-2024:
        
        Event: {event_description}
        Category: {category}
        Scope: {scope}
        
        Focus on identifying parallels to:
        1. Market manipulation incidents
        2. Social control mechanisms
        3. Technological disruptions
        4. Power consolidation patterns
        
        Format your response as a list of historical events with brief explanations.
        """
        
        parallels_response = await self.llm.ainvoke([
            SystemMessage(content="You are Dr. Gonzo's pattern recognition system."),
            HumanMessage(content=parallels_prompt)
        ])
        
        # Find similar historical events
        historical_matches = await self.find_historical_parallels(
            event_description,
            category,
            scope
        )
        
        # Match against future chains
        matched_chains = await self.match_to_future_chains(
            event_description,
            historical_matches,
            category
        )
        
        # Use LLM to generate warnings
        warnings_prompt = f"""
        As Dr. Gonzo, analyze these patterns and generate specific warnings:
        
        Current Event: {event_description}
        Historical Parallels: {parallels_response.content}
        
        Based on your knowledge of the dystopian future of 3030, what specific warnings 
        would you give about where these patterns might lead?
        """
        
        warnings_response = await self.llm.ainvoke([
            SystemMessage(content="You are Dr. Gonzo's warning system."),
            HumanMessage(content=warnings_prompt)
        ])
        
        warnings = [
            warn.strip()
            for warn in warnings_response.content.split('\n')
            if warn.strip()
        ]
        
        # Use LLM to generate prevention strategies
        strategies_prompt = f"""
        As Dr. Gonzo, provide specific strategies to prevent these patterns from leading to the dystopian future:
        
        Current Event: {event_description}
        Warnings: {warnings_response.content}
        
        What concrete actions can be taken to disrupt these patterns?
        """
        
        strategies_response = await self.llm.ainvoke([
            SystemMessage(content="You are Dr. Gonzo's strategic planning system."),
            HumanMessage(content=strategies_prompt)
        ])
        
        strategies = [
            strat.strip()
            for strat in strategies_response.content.split('\n')
            if strat.strip()
        ]
        
        # Calculate confidence based on matches and LLM responses
        base_confidence = self._calculate_confidence(
            historical_matches,
            matched_chains
        )
        
        # Adjust confidence based on LLM analysis depth
        llm_confidence = min(
            (len(warnings) * 0.2 + len(strategies) * 0.2),
            0.6  # Cap LLM contribution
        )
        
        final_confidence = min(base_confidence + llm_confidence, 1.0)
        
        return CausalAnalysis(
            current_event=event_description,
            timestamp=current_date,
            historical_parallels=historical_matches,
            matched_chains=matched_chains,
            warnings=warnings,
            prevention_strategies=strategies,
            confidence=final_confidence,
            metadata=metadata or {}
        )
    
    async def find_historical_parallels(
        self,
        event: str,
        category: EventCategory,
        scope: EventScope
    ) -> List[CausalEvent]:
        """Find similar events from pre-2024."""
        matches = []
        for stored_event in self.events.values():
            if stored_event.timestamp.year < 2024:
                if (
                    stored_event.category == category
                    and stored_event.scope == scope
                ):
                    matches.append(stored_event)
        return matches
    
    async def match_to_future_chains(
        self,
        event: str,
        historical: List[CausalEvent],
        category: EventCategory
    ) -> List[TimelineChain]:
        """Find chains that match current patterns."""
        matches = []
        for chain in self.event_chains.values():
            if category in chain.categories:
                matches.append(chain)
        return matches
    
    def _calculate_confidence(
        self,
        historical: List[CausalEvent],
        chains: List[TimelineChain]
    ) -> float:
        """Calculate base confidence score for the analysis."""
        if not historical or not chains:
            return 0.3  # Base confidence level
            
        # Average confidence of historical matches
        hist_conf = sum(e.confidence for e in historical) / len(historical)
        
        # Number of matching chains affects confidence
        chain_factor = min(len(chains) / 3, 1.0)  # Cap at 1.0
        
        return hist_conf * chain_factor