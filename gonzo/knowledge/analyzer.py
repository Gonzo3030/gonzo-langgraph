"""Core knowledge base for media analysis."""

from typing import Dict, List, Optional
from .types import TacticType, MediaType
from .models import (
    ManipulationTactic, 
    NarrativeTechnique, 
    DeepStatePattern,
    PropagandaFramework, 
    Example
)

class MediaAnalyzer:
    """Core knowledge base for media analysis."""
    
    def __init__(self):
        self.manipulation_tactics: Dict[str, ManipulationTactic] = {}
        self.narrative_techniques: Dict[str, NarrativeTechnique] = {}
        self.deep_state_patterns: Dict[str, DeepStatePattern] = {}
        self.propaganda_frameworks: Dict[str, PropagandaFramework] = {}
        self.examples: List[Example] = []
        
    def add_manipulation_tactic(self, tactic: ManipulationTactic) -> None:
        """Add a manipulation tactic to the knowledge base."""
        self.manipulation_tactics[tactic.name] = tactic
        
    def add_narrative_technique(self, technique: NarrativeTechnique) -> None:
        """Add a narrative technique to the knowledge base."""
        self.narrative_techniques[technique.name] = technique
        
    def add_deep_state_pattern(self, pattern: DeepStatePattern) -> None:
        """Add a deep state pattern to the knowledge base."""
        self.deep_state_patterns[pattern.name] = pattern
        
    def add_propaganda_framework(self, framework: PropagandaFramework) -> None:
        """Add a propaganda framework to the knowledge base."""
        self.propaganda_frameworks[framework.name] = framework
        
    def add_example(self, example: Example) -> None:
        """Add an example to the knowledge base."""
        self.examples.append(example)
        
    def get_tactics_by_type(self, tactic_type: TacticType) -> List[ManipulationTactic]:
        """Get all tactics of a specific type."""
        return [t for t in self.manipulation_tactics.values() if t.type == tactic_type]
        
    def get_examples_by_tactic(self, tactic_type: TacticType) -> List[Example]:
        """Get all examples that demonstrate a specific tactic."""
        examples = []
        for tactic in self.manipulation_tactics.values():
            if tactic.type == tactic_type:
                examples.extend(tactic.examples)
        return examples

    def analyze_content(self, 
        text: str,
        source_type: MediaType,
        context: Optional[str] = None
    ) -> Dict:
        """Analyze a piece of media content using the knowledge base.
        
        Args:
            text: The media content text
            source_type: Type of media source
            context: Optional context about the piece
            
        Returns:
            Analysis results including identified tactics and patterns
        """
        results = {
            "identified_tactics": [],
            "narrative_elements": [],
            "propaganda_indicators": [],
            "deep_state_signals": [],
            "confidence_scores": {}
        }
        
        # Check for manipulation tactics
        for tactic in self.manipulation_tactics.values():
            confidence = self._check_tactic_indicators(text, tactic)
            if confidence > 0.5:
                results["identified_tactics"].append({
                    "tactic": tactic.name,
                    "confidence": confidence,
                    "indicators_found": self._find_matching_indicators(text, tactic)
                })
        
        # Look for narrative patterns
        for technique in self.narrative_techniques.values():
            if self._check_narrative_elements(text, technique):
                results["narrative_elements"].append({
                    "technique": technique.name,
                    "phases_identified": self._identify_narrative_phases(text, technique)
                })
        
        # Check propaganda frameworks
        for framework in self.propaganda_frameworks.values():
            if source_type in framework.distribution_channels:
                matches = self._check_propaganda_framework(text, framework)
                if matches:
                    results["propaganda_indicators"].extend(matches)
                    
        # Analyze deep state patterns
        for pattern in self.deep_state_patterns.values():
            signals = self._check_deep_state_pattern(text, pattern)
            if signals:
                results["deep_state_signals"].extend(signals)
        
        return results
    
    def _check_tactic_indicators(self, text: str, tactic: ManipulationTactic) -> float:
        """Check how many of a tactic's indicators are present."""
        matches = 0
        for indicator in tactic.indicators:
            if indicator.lower() in text.lower():
                matches += 1
        return matches / len(tactic.indicators) if tactic.indicators else 0.0
    
    def _find_matching_indicators(self, text: str, tactic: ManipulationTactic) -> List[str]:
        """Find which specific indicators from a tactic are present."""
        return [i for i in tactic.indicators if i.lower() in text.lower()]
    
    def _check_narrative_elements(self, text: str, technique: NarrativeTechnique) -> bool:
        """Check if a narrative technique's elements are present."""
        for hint in technique.identification_hints:
            if hint.lower() in text.lower():
                return True
        return False
    
    def _identify_narrative_phases(self, text: str, technique: NarrativeTechnique) -> List[str]:
        """Identify which narrative phases are present."""
        present_phases = []
        for phase in technique.phases:
            # Add phase detection logic here
            pass
        return present_phases
    
    def _check_propaganda_framework(self, text: str, framework: PropagandaFramework) -> List[Dict]:
        """Check if elements of a propaganda framework are present."""
        matches = []
        # Add propaganda framework detection logic here
        return matches
    
    def _check_deep_state_pattern(self, text: str, pattern: DeepStatePattern) -> List[Dict]:
        """Check if deep state pattern indicators are present."""
        signals = []
        # Add deep state pattern detection logic here
        return signals