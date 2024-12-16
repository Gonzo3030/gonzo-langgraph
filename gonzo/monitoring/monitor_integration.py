"""Integration of monitoring systems with Gonzo's main workflow."""
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..state_management import UnifiedState
from ..causality.analyzer import CausalAnalyzer
from .market_monitor import CryptoMarketMonitor
from .social_monitor import SocialMediaMonitor
from .real_time_monitor import RealTimeMonitor, MonitoringResult

class MonitoringSystem:
    """Integrated monitoring system for Gonzo."""
    
    def __init__(self, state: UnifiedState):
        # Initialize analyzers
        self.causal_analyzer = CausalAnalyzer()
        
        # Initialize monitors
        self.market_monitor = CryptoMarketMonitor(
            api_key=state.memory.retrieve("api_credentials", "long_term")["crypto_compare_key"]
        )
        
        x_creds = state.x_integration.direct_api
        self.social_monitor = SocialMediaMonitor(
            api_key=x_creds["api_key"],
            api_secret=x_creds["api_secret"],
            access_token=x_creds["access_token"],
            access_secret=x_creds["access_secret"]
        )
        
        # Initialize real-time monitor with causal analyzer
        self.monitor = RealTimeMonitor(self.causal_analyzer)
    
    async def update_state(self, state: UnifiedState) -> UnifiedState:
        """Update state with new monitoring data."""
        try:
            # Run market monitoring
            market_events = await self.market_monitor.check_markets()
            
            # Run social monitoring
            social_events = await self.social_monitor.monitor_social_activity()
            
            # Get monitoring results with causal analysis
            results = await self.monitor.monitor_cycle()
            
            # Update state with monitoring results
            if market_events:
                state.knowledge_graph.entities.update({
                    f"market_event_{event.timestamp.isoformat()}": event.__dict__
                    for event in market_events
                })
            
            if social_events:
                state.knowledge_graph.entities.update({
                    f"social_event_{event.timestamp.isoformat()}": event.__dict__
                    for event in social_events
                })
            
            # Add causal analyses to state
            for analysis in results.analyses:
                state.assessment.content_analysis[f"causal_{datetime.utcnow().isoformat()}"] = {
                    "type": "causal_analysis",
                    "historical_parallels": [e.__dict__ for e in analysis.historical_parallels],
                    "warnings": analysis.warnings,
                    "prevention_strategies": analysis.prevention_strategies,
                    "confidence": analysis.confidence
                }
            
            # Queue high-confidence analyses for narrative generation
            significant_analyses = [
                a for a in results.analyses 
                if a.confidence > 0.7
            ]
            
            if significant_analyses:
                state.narrative.context.update({
                    "pending_analyses": [
                        {
                            "analysis": a.__dict__,
                            "timestamp": datetime.utcnow().isoformat()
                        }
                        for a in significant_analyses
                    ]
                })
            
            return state
            
        except Exception as e:
            state.record_error(f"Monitoring error: {str(e)}")
            return state