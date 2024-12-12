from typing import Dict, List, Any, Optional
from datetime import datetime, UTC
from pathlib import Path
from langchain_core.language_models import BaseLLM
from langchain_core.prompts import ChatPromptTemplate

from .metrics import EvolutionMetrics
from .memory import ContentMemoryManager
from .state import EvolutionStateManager
from ..patterns.detector import PatternDetector
from ..types import TimeAwareEntity

class GonzoEvolutionSystem:
    """Core system for managing Gonzo's evolution and learning"""
    
    def __init__(self, 
                 llm: BaseLLM,
                 pattern_detector: PatternDetector,
                 storage_path: Optional[Path] = None):
        self.llm = llm
        self.pattern_detector = pattern_detector
        self.content_memory = ContentMemoryManager(storage_path / 'content' if storage_path else None)
        self.evolution_state = EvolutionStateManager(storage_path / 'evolution' if storage_path else None)
        
    async def process_youtube_content(self, analysis_result: Dict[str, Any]):
        """Process analyzed YouTube content for evolution
        
        Args:
            analysis_result: Results from YouTubeCollector.analyze_content()
        """
        if analysis_result.get('error'):
            return
            
        # Extract entities and patterns
        entities = analysis_result.get('entities', [])
        segments = analysis_result.get('segments', [])
        patterns = analysis_result.get('patterns', [])
        
        # Store processed content
        await self.content_memory.store_content(
            content_type="youtube",
            entities=entities,
            segments=segments,
            patterns=patterns,
            timestamp=datetime.now(UTC)
        )
        
        # Update pattern recognition
        await self.evolution_state.update_patterns(patterns)
        
        # Evolve understanding
        await self.evolve_perspective()
    
    async def evolve_perspective(self):
        """Evolve Gonzo's understanding based on accumulated data"""
        # Get recent patterns and historical context
        recent_patterns = await self.evolution_state.get_recent_patterns()
        historical_context = await self.content_memory.get_historical_context()
        
        # Update evolution metrics
        evolution_metrics = await self.evolution_state.update_evolution_metrics(
            recent_patterns=recent_patterns,
            historical_context=historical_context
        )
        
        # Adjust response generation based on evolution metrics
        await self.update_response_patterns(evolution_metrics)
    
    async def update_response_patterns(self, metrics: EvolutionMetrics):
        """Update response generation based on evolution metrics
        
        Args:
            metrics: Current evolution metrics
        """
        # Build evolution context for response generation
        evolution_context = {
            'pattern_confidence': metrics.pattern_confidence,
            'narrative_consistency': metrics.narrative_consistency,
            'prediction_accuracy': metrics.prediction_accuracy,
            'temporal_connections': metrics.temporal_connections
        }
        
        # Update pattern detector with evolved understanding
        self.pattern_detector.update_detection_parameters(
            confidence_threshold=metrics.pattern_confidence,
            temporal_weight=sum(metrics.temporal_connections.values()) / len(metrics.temporal_connections) 
                if metrics.temporal_connections else 0.5
        )
        
    async def get_current_metrics(self) -> EvolutionMetrics:
        """Get current evolution metrics"""
        return await self.evolution_state.get_current_metrics()
        
    async def analyze_entities(self, entities: List[TimeAwareEntity]) -> Dict[str, Any]:
        """Analyze a set of entities for patterns and relationships
        
        Args:
            entities: List of entities to analyze
            
        Returns:
            Analysis results
        """
        # Use pattern detector to analyze entities
        patterns = self.pattern_detector.detect_patterns(entities)
        
        # Get current evolution metrics
        metrics = await self.get_current_metrics()
        
        # Enhance pattern detection with evolution context
        enhanced_patterns = []
        for pattern in patterns:
            # Add confidence based on evolution metrics
            pattern['confidence'] = pattern.get('confidence', 0.5) * metrics.pattern_confidence
            
            # Add temporal context if available
            if 'temporal_key' in pattern and pattern['temporal_key'] in metrics.temporal_connections:
                pattern['temporal_strength'] = metrics.temporal_connections[pattern['temporal_key']]
                
            enhanced_patterns.append(pattern)
            
        return {
            'patterns': enhanced_patterns,
            'metrics': metrics.__dict__
        }
