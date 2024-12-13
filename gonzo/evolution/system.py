from typing import Dict, List, Any, Optional
from datetime import datetime, UTC
from pathlib import Path
from langchain_core.language_models import BaseLLM
from langchain_core.prompts import ChatPromptTemplate

from .metrics import EvolutionMetrics
from .memory import ContentMemoryManager
from .state import EvolutionStateManager
from ..types import TimeAwareEntity, GonzoState
from ..nodes.pattern_detection import detect_patterns

class GonzoEvolutionSystem:
    """Core system for managing Gonzo's evolution and learning"""
    
    def __init__(self, 
                 llm: BaseLLM,
                 storage_path: Optional[Path] = None):
        """Initialize evolution system.
        
        Args:
            llm: Language model for analysis
            storage_path: Optional path for storing evolution data
        """
        self.llm = llm
        self.content_memory = ContentMemoryManager(storage_path / 'content' if storage_path else None)
        self.evolution_state = EvolutionStateManager(storage_path / 'evolution' if storage_path else None)
        
    async def process_youtube_content(self, state: GonzoState):
        """Process analyzed YouTube content for evolution
        
        Args:
            state: Current Gonzo state
        """
        # Extract entities and patterns from state
        entities = state.analysis.entities
        patterns = state.analysis.patterns
        
        # Store processed content
        await self.content_memory.store_content(
            content_type="youtube",
            entities=entities,
            patterns=patterns,
            timestamp=datetime.now(UTC)
        )
        
        # Update pattern recognition
        await self.evolution_state.update_patterns(patterns)
        
        # Evolve understanding
        await self.evolve_perspective()
        
        # Update state evolution metrics
        metrics = await self.evolution_state.get_current_metrics()
        state.evolution.pattern_confidence = metrics.pattern_confidence
        state.evolution.narrative_consistency = metrics.narrative_consistency
        state.evolution.prediction_accuracy = metrics.prediction_accuracy
    
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
        
        # Store evolution context for later use
        await self.evolution_state.store_context(evolution_context)
        
    async def get_current_metrics(self) -> EvolutionMetrics:
        """Get current evolution metrics"""
        return await self.evolution_state.get_current_metrics()
        
    async def analyze_entities(self, state: GonzoState) -> Dict[str, Any]:
        """Analyze entities in state for patterns and relationships
        
        Args:
            state: Current Gonzo state
            
        Returns:
            Analysis results
        """
        # Use pattern detection node
        pattern_result = await detect_patterns(state, self.llm)
        state = pattern_result["state"]
        
        # Get current evolution metrics
        metrics = await self.get_current_metrics()
        
        # Enhance patterns with evolution context
        enhanced_patterns = []
        for pattern in state.analysis.patterns:
            # Add confidence based on evolution metrics
            pattern['confidence'] = pattern.get('confidence', 0.5) * metrics.pattern_confidence
            
            # Add temporal context if available
            if 'temporal_key' in pattern and pattern['temporal_key'] in metrics.temporal_connections:
                pattern['temporal_strength'] = metrics.temporal_connections[pattern['temporal_key']]
                
            enhanced_patterns.append(pattern)
            
        # Update state
        state.analysis.patterns = enhanced_patterns
        state.evolution.pattern_confidence = metrics.pattern_confidence
        state.evolution.narrative_consistency = metrics.narrative_consistency
        state.evolution.prediction_accuracy = metrics.prediction_accuracy
            
        return {
            'patterns': enhanced_patterns,
            'metrics': metrics.__dict__
        }
