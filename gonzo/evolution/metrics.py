from dataclasses import dataclass
from typing import Dict

@dataclass
class EvolutionMetrics:
    """Metrics tracking the evolution of Gonzo's understanding and effectiveness"""
    pattern_confidence: float  # Confidence in identified patterns
    narrative_consistency: float  # Consistency of narrative analysis
    prediction_accuracy: float  # Accuracy of predictions
    temporal_connections: Dict[str, float]  # Strength of temporal connections between events
    
    @classmethod
    def create_default(cls) -> 'EvolutionMetrics':
        """Create metrics with default values"""
        return cls(
            pattern_confidence=0.5,
            narrative_consistency=0.5,
            prediction_accuracy=0.5,
            temporal_connections={}
        )
    
    def update_with_results(self, 
                           pattern_results: float = None,
                           narrative_results: float = None,
                           prediction_results: float = None,
                           temporal_updates: Dict[str, float] = None):
        """Update metrics with new results"""
        if pattern_results is not None:
            self.pattern_confidence = (
                0.8 * self.pattern_confidence + 0.2 * pattern_results
            )
            
        if narrative_results is not None:
            self.narrative_consistency = (
                0.8 * self.narrative_consistency + 0.2 * narrative_results
            )
            
        if prediction_results is not None:
            self.prediction_accuracy = (
                0.8 * self.prediction_accuracy + 0.2 * prediction_results
            )
            
        if temporal_updates:
            for key, value in temporal_updates.items():
                if key in self.temporal_connections:
                    self.temporal_connections[key] = (
                        0.8 * self.temporal_connections[key] + 0.2 * value
                    )
                else:
                    self.temporal_connections[key] = value