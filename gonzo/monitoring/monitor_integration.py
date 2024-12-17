"""Integration of monitoring systems with Gonzo's main workflow."""
from typing import Dict, Any
from datetime import datetime

from ..state_management import UnifiedState
from .social_monitor import SocialMediaMonitor
from .market_monitor import CryptoMarketMonitor

class MonitoringSystem:
    """Integrated monitoring system for Gonzo."""
    
    def __init__(self, state: UnifiedState):
        # Initialize social media monitoring
        self.social_monitor = SocialMediaMonitor(
            api_key=state.x_integration.direct_api['api_key'],
            api_secret=state.x_integration.direct_api['api_secret'],
            access_token=state.x_integration.direct_api['access_token'],
            access_secret=state.x_integration.direct_api['access_secret']
        )
        
        # Initialize market monitoring
        api_creds = state.memory.retrieve("api_credentials", "long_term") or {}
        self.market_monitor = CryptoMarketMonitor(
            api_key=api_creds.get('crypto_compare_key', '')
        )
    
    async def update_state(self, state: UnifiedState) -> UnifiedState:
        """Update state with new monitoring data."""
        try:
            # Get social media updates
            social_events = await self.social_monitor.monitor_social_activity()
            
            # Get market updates
            market_events = await self.market_monitor.check_markets()
            
            # Update state with new data
            if social_events:
                state.knowledge_graph.entities.update({
                    f"social_event_{event.timestamp.isoformat()}": event.__dict__
                    for event in social_events
                })
            
            if market_events:
                state.knowledge_graph.entities.update({
                    f"market_event_{event.timestamp.isoformat()}": event.__dict__
                    for event in market_events
                })
            
            # Add to pending analyses if we have significant events
            if social_events or market_events:
                state.narrative.context["pending_analyses"] = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "social_events": [e.__dict__ for e in social_events],
                    "market_events": [e.__dict__ for e in market_events]
                }
            
            return state
            
        except Exception as e:
            state.record_error(f"Monitoring error: {str(e)}")
            return state