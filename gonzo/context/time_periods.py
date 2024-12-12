from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass

@dataclass
class TimePeriodContext:
    start_year: int
    end_year: int
    key_events: List[str]
    themes: List[str]
    significance: float  # How relevant this period is to current analysis

class TimePeriodManager:
    """Manages historical context and time period connections"""
    
    def __init__(self):
        # Initialize with core time periods
        self.time_periods = {
            "past": TimePeriodContext(
                start_year=1992,
                end_year=1992,
                key_events=[
                    "Cable news reshaping reality",
                    "Rise of media manipulation",
                    "Early internet emergence"
                ],
                themes=[
                    "Media control",
                    "Information manipulation",
                    "Technological transition"
                ],
                significance=0.0
            ),
            "present": TimePeriodContext(
                start_year=2024,
                end_year=2024,
                key_events=[
                    "AI revolution",
                    "Digital reality manipulation",
                    "Tech oligarchy"
                ],
                themes=[
                    "AI influence",
                    "Reality distortion",
                    "Corporate control"
                ],
                significance=0.0
            ),
            "future": TimePeriodContext(
                start_year=3030,
                end_year=3030,
                key_events=[
                    "Digital Dystopia",
                    "Reality as product",
                    "Technological enslavement"
                ],
                themes=[
                    "Total control",
                    "Lost humanity",
                    "Corporate dominance"
                ],
                significance=0.0
            )
        }
        
    def analyze_temporal_connections(self, 
        content: Dict[str, Any],
        evolution_metrics: Dict[str, Any]
    ) -> Dict[str, float]:
        """Analyze content for connections to different time periods"""
        connections = {}
        
        # Reset significance scores
        for period in self.time_periods.values():
            period.significance = 0.0
        
        # Check for theme matches
        for period_name, period in self.time_periods.items():
            theme_matches = 0
            for theme in period.themes:
                if any(theme.lower() in str(v).lower() for v in content.values()):
                    theme_matches += 1
            
            # Calculate significance
            if theme_matches:
                period.significance = theme_matches / len(period.themes)
                connections[period_name] = period.significance
        
        return connections
    
    def get_relevant_context(self, 
        min_significance: float = 0.3
    ) -> Dict[str, TimePeriodContext]:
        """Get time periods relevant to current analysis"""
        return {
            name: period 
            for name, period in self.time_periods.items() 
            if period.significance >= min_significance
        }
    
    def build_historical_context(self,
        connections: Dict[str, float]
    ) -> str:
        """Build narrative connecting relevant time periods"""
        context_parts = []
        
        for period_name, significance in connections.items():
            if significance >= 0.3:  # Only include significant connections
                period = self.time_periods[period_name]
                context_parts.append(
                    f"{period.start_year}: {', '.join(period.key_events)}"
                )
        
        if context_parts:
            return " → ".join(context_parts)
        return ""