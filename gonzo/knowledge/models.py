"""Models for media analysis knowledge base."""

from typing import List
from datetime import datetime
from pydantic import BaseModel, Field

from .types import TacticType, MediaType, NarrativePhase

class Example(BaseModel):
    """Media manipulation example with context."""
    description: str
    source: str
    date: datetime
    context: str
    tactics_used: List[TacticType]
    impact: str
    counter_analysis: str

class ManipulationTactic(BaseModel):
    """Detailed description of a media manipulation tactic."""
    type: TacticType
    name: str
    description: str
    indicators: List[str]
    examples: List[Example]
    counter_techniques: List[str]
    common_phrases: List[str]
    typical_sources: List[MediaType]
    effectiveness_rating: float = Field(ge=0.0, le=1.0)

class NarrativeTechnique(BaseModel):
    """Analysis of narrative construction and deployment."""
    name: str
    description: str
    phases: List[NarrativePhase]
    tactics_employed: List[TacticType]
    examples: List[Example]
    identification_hints: List[str]
    counter_narratives: List[str]

class DeepStatePattern(BaseModel):
    """Patterns related to deep state operations and influence."""
    pattern_name: str
    description: str
    indicators: List[str]
    typical_narratives: List[str]
    historical_examples: List[Example]
    media_coordination: List[str]
    power_structures: List[str]

class PropagandaFramework(BaseModel):
    """Framework for analyzing propaganda techniques."""
    name: str
    description: str
    primary_tactics: List[TacticType]
    target_audience: List[str]
    psychological_drivers: List[str]
    distribution_channels: List[MediaType]
    examples: List[Example]