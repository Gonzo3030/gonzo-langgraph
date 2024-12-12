from typing import Dict, List, Any, Optional
from datetime import datetime, UTC
import json
from pathlib import Path
from .metrics import EvolutionMetrics

class EvolutionStateManager:
    """Manages the evolution state and metrics"""
    
    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path('evolution_state')
        self.storage_path.mkdir(exist_ok=True)
        self.current_metrics = EvolutionMetrics.create_default()
        self._load_latest_state()
        
    def _load_latest_state(self):
        """Load the most recent evolution state"""
        state_files = list(self.storage_path.glob('*.json'))
        if state_files:
            latest_file = max(state_files, key=lambda p: p.stat().st_mtime)
            with open(latest_file) as f:
                state_data = json.load(f)
                self.current_metrics = EvolutionMetrics(
                    pattern_confidence=state_data['pattern_confidence'],
                    narrative_consistency=state_data['narrative_consistency'],
                    prediction_accuracy=state_data['prediction_accuracy'],
                    temporal_connections=state_data['temporal_connections']
                )
                
    async def update_patterns(self, patterns: List[Dict[str, Any]]):
        """Update pattern recognition based on new data"""
        # Calculate pattern confidence based on new patterns
        pattern_confidence = sum(p.get('confidence', 0.5) for p in patterns) / len(patterns) if patterns else 0.5
        
        # Update metrics
        self.current_metrics.update_with_results(pattern_results=pattern_confidence)
        
        # Save updated state
        self._save_current_state()
        
    async def get_current_metrics(self) -> EvolutionMetrics:
        """Get current evolution metrics"""
        return self.current_metrics
    
    async def get_recent_patterns(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get recently identified patterns"""
        patterns = []
        current = datetime.now(UTC)
        
        # Load recent pattern files
        for day in range(days):
            date_path = self.storage_path / 'patterns' / current.strftime('%Y/%m/%d')
            if date_path.exists():
                for file_path in date_path.glob('*.json'):
                    with open(file_path) as f:
                        patterns.extend(json.load(f))
                        
        return patterns
    
    async def update_evolution_metrics(
        self,
        recent_patterns: List[Dict[str, Any]],
        historical_context: List[Dict[str, Any]]
    ) -> EvolutionMetrics:
        """Update evolution metrics based on new data and historical context"""
        # Calculate new pattern confidence
        pattern_confidence = sum(p.get('confidence', 0.5) for p in recent_patterns) / len(recent_patterns) if recent_patterns else 0.5
        
        # Calculate narrative consistency
        narrative_scores = []
        for context in historical_context:
            if context.get('narrative_score'):
                narrative_scores.append(context['narrative_score'])
        narrative_consistency = sum(narrative_scores) / len(narrative_scores) if narrative_scores else 0.5
        
        # Update temporal connections
        temporal_updates = {}
        for pattern in recent_patterns:
            if 'temporal_connection' in pattern:
                key = pattern['temporal_connection']['key']
                temporal_updates[key] = pattern['temporal_connection']['strength']
        
        # Update metrics
        self.current_metrics.update_with_results(
            pattern_results=pattern_confidence,
            narrative_results=narrative_consistency,
            temporal_updates=temporal_updates
        )
        
        # Save updated state
        self._save_current_state()
        
        return self.current_metrics
    
    def _save_current_state(self):
        """Save current evolution state"""
        timestamp = datetime.now(UTC)
        file_path = self.storage_path / f'state_{timestamp.strftime("%Y%m%d_%H%M%S")}.json'
        
        state_data = {
            'timestamp': timestamp.isoformat(),
            'pattern_confidence': self.current_metrics.pattern_confidence,
            'narrative_consistency': self.current_metrics.narrative_consistency,
            'prediction_accuracy': self.current_metrics.prediction_accuracy,
            'temporal_connections': self.current_metrics.temporal_connections
        }
        
        with open(file_path, 'w') as f:
            json.dump(state_data, f, indent=2)