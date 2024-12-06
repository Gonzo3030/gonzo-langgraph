from typing import Dict, Any, List
from datetime import datetime
from .base import BaseNode
from ...types import GonzoState, update_state

class AnalysisNode(BaseNode):
    """Base class for analysis nodes that process different types of content.
    
    Provides common analysis functionality while allowing specialized processing
    for different domains (market data, narratives, causality).
    """
    
    def __init__(self, analysis_type: str, config: Dict[str, Any] = None):
        super().__init__(config)
        self.analysis_type = analysis_type
        
    def validate_state(self, state: GonzoState) -> bool:
        """Validate state has required content for analysis."""
        return (
            'category' in state 
            and (state['category'] == self.analysis_type 
                 or state.get(f'requires_{self.analysis_type}_analysis', False))
        )

class MarketAnalysisNode(AnalysisNode):
    """Analyzes market data through lens of preventing dystopian future.
    
    Focuses on:
    - Crypto market movements
    - Centralization vs decentralization trends
    - Power concentration patterns
    - Market manipulation indicators
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__('market', config)
        
    def _process(self, state: GonzoState) -> GonzoState:
        """Process market-related state updates.
        
        Args:
            state: Current state
            
        Returns:
            Updated state with market analysis
        """
        updates = {
            'market_analysis_completed': True,
            'market_analysis_timestamp': datetime.now().isoformat(),
            'steps': state.get('steps', []) + ['market_analysis']
        }
        
        return update_state(state, updates)

class NarrativeAnalysisNode(AnalysisNode):
    """Analyzes narratives for manipulation and control patterns.
    
    Focuses on:
    - Media bias and propaganda
    - Corporate/state influence
    - Historical parallels
    - Future implications
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__('narrative', config)
        
    def _process(self, state: GonzoState) -> GonzoState:
        """Process narrative-related state updates.
        
        Args:
            state: Current state
            
        Returns:
            Updated state with narrative analysis
        """
        updates = {
            'narrative_analysis_completed': True,
            'narrative_analysis_timestamp': datetime.now().isoformat(),
            'steps': state.get('steps', []) + ['narrative_analysis']
        }
        
        return update_state(state, updates)

class CausalityAnalysisNode(AnalysisNode):
    """Analyzes cause-effect relationships across time periods.
    
    Focuses on:
    - Connecting current events to future outcomes
    - Identifying manipulation patterns
    - Tracking power structure evolution
    - Mapping path to dystopian future
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__('causality', config)
        
    def _process(self, state: GonzoState) -> GonzoState:
        """Process causality-related state updates.
        
        Args:
            state: Current state
            
        Returns:
            Updated state with causality analysis
        """
        updates = {
            'causality_analysis_completed': True,
            'causality_analysis_timestamp': datetime.now().isoformat(),
            'steps': state.get('steps', []) + ['causality_analysis']
        }
        
        return update_state(state, updates)