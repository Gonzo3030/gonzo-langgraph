from enum import Enum
from typing import Optional, Dict, Any
from dataclasses import dataclass

class ResponseType(Enum):
    QUICK_TAKE = "quick_take"
    THREAD_ANALYSIS = "thread_analysis"
    HISTORICAL_BRIDGE = "historical_bridge"
    INTERACTION = "interaction"

@dataclass
class ResponseConfig:
    max_length: Optional[int]
    style: str
    use_case: str

class ResponseTypeManager:
    """Manages different types of responses and their configurations"""
    
    def __init__(self):
        self.response_types = {
            ResponseType.QUICK_TAKE: ResponseConfig(
                max_length=280,
                style="punchy, immediate reactions",
                use_case="rapid responses, observations"
            ),
            ResponseType.THREAD_ANALYSIS: ResponseConfig(
                max_length=None,
                style="full gonzo flow",
                use_case="deep dives, pattern analysis"
            ),
            ResponseType.HISTORICAL_BRIDGE: ResponseConfig(
                max_length=560,  # 2 tweets
                style="connecting past-present-future",
                use_case="drawing parallels across time"
            ),
            ResponseType.INTERACTION: ResponseConfig(
                max_length=280,
                style="gonzo personality, direct engagement",
                use_case="replies, conversations"
            )
        }
        
    def select_response_type(self, 
        content: Dict[str, Any],
        evolution_metrics: Dict[str, Any]
    ) -> ResponseType:
        """Select appropriate response type based on content and evolution state"""
        # Higher pattern confidence suggests deeper analysis needed
        pattern_confidence = evolution_metrics.get('pattern_confidence', 0.5)
        
        # Check for historical connections
        has_temporal_connections = bool(evolution_metrics.get('temporal_connections', {}))
        
        # Determine if content warrants full analysis
        is_significant = (
            pattern_confidence > 0.7 or
            content.get('requires_analysis', False)
        )
        
        # Select type based on factors
        if has_temporal_connections:
            return ResponseType.HISTORICAL_BRIDGE
        elif is_significant:
            return ResponseType.THREAD_ANALYSIS
        else:
            return ResponseType.QUICK_TAKE
            
    def get_config(self, response_type: ResponseType) -> ResponseConfig:
        """Get configuration for a response type"""
        return self.response_types[response_type]