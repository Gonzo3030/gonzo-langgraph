"""Core types for media analysis knowledge base."""

from enum import Enum

class TacticType(str, Enum):
    """Types of media manipulation tactics."""
    NARRATIVE_CONTROL = "narrative_control"
    FEAR_BASED = "fear_based"
    AUTHORITY_APPEAL = "authority_appeal"
    DISTRACTION = "distraction"
    FRAMING = "framing"
    OMISSION = "omission"
    LOADED_LANGUAGE = "loaded_language"
    FALSE_BALANCE = "false_balance"
    CONTROLLED_OPPOSITION = "controlled_opposition"

class MediaType(str, Enum):
    """Types of media sources."""
    MAINSTREAM = "mainstream"
    INDEPENDENT = "independent"
    CORPORATE = "corporate"
    STATE = "state"
    ALTERNATIVE = "alternative"

class NarrativePhase(str, Enum):
    """Phases of narrative deployment."""
    SEEDING = "seeding"
    AMPLIFICATION = "amplification"
    REINFORCEMENT = "reinforcement"
    CONSENSUS = "consensus"
    MARGINALIZATION = "marginalization"