"""Real-time monitoring system for Gonzo."""
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass

from ..state_management import UnifiedState, MarketData, SocialData
from ..causality.types import EventCategory, EventScope
from ..causality.analyzer import CausalAnalyzer, CausalAnalysis

@dataclass
class MarketEvent:
    symbol: str
    price: float
    volume: float
    timestamp: datetime
    indicators: Dict[str, float]
    metadata: Dict[str, Any]

@dataclass
class SocialEvent:
    content: str
    author: str
    timestamp: datetime
    platform: str
    engagement: Dict[str, int]
    sentiment: float
    metadata: Dict[str, Any]

class RealTimeMonitor:
    """Monitors and analyzes real-time data streams."""
    
    def __init__(self, state: UnifiedState, market_monitor: Any, social_monitor: Any, causal_analyzer: CausalAnalyzer):
        self.state = state
        self.market_monitor = market_monitor
        self.social_monitor = social_monitor
        self.causal_analyzer = causal_analyzer
        self.last_market_check = None
        self.last_social_check = None
    
    async def update_state(self, state: UnifiedState) -> UnifiedState:
        """Update all monitoring data in the state."""
        try:
            # Update market data
            state = await self.market_monitor.update_market_state(state)
            self.last_market_check = datetime.utcnow()
            
            # Update social data
            if self.social_monitor:
                state = await self.social_monitor.update_social_state(state)
                self.last_social_check = datetime.utcnow()
            
            # Analyze if we have pending events
            if state.narrative.pending_analyses:
                await self.analyze_current_events(state)
            
            return state
            
        except Exception as e:
            print(f"Error in monitoring cycle: {str(e)}")
            state.api_errors.append(f"Monitoring cycle error: {str(e)}")
            return state
    
    async def analyze_current_events(self, state: UnifiedState) -> None:
        """Analyze current market and social events."""
        try:
            # Combine all events for analysis
            all_events = (
                state.narrative.market_events +
                state.narrative.social_events
            )
            
            # Analyze each event
            for event in all_events:
                analysis = await self.causal_analyzer.analyze_current_event(
                    event_description=str(event),
                    category=EventCategory.MARKET if "price" in event else EventCategory.SOCIAL,
                    scope=EventScope.CRYPTOCURRENCY,
                    current_date=datetime.utcnow(),
                    metadata=event.get("metadata", {})
                )
                
                if analysis:
                    state.analysis.correlations.append(analysis.__dict__)
            
            # Clear pending analyses flag
            state.narrative.pending_analyses = False
            
        except Exception as e:
            print(f"Analysis error: {str(e)}")
            state.api_errors.append(f"Event analysis error: {str(e)}")