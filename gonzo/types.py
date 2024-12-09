from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID
from enum import Enum, auto
from pydantic import BaseModel, Field

class EntityType(str, Enum):
    """Types of entities that can be extracted."""
    PERSON = "PERSON"
    ORGANIZATION = "ORGANIZATION"
    CONCEPT = "CONCEPT"
    CLAIM = "CLAIM"
    NARRATIVE = "NARRATIVE"
    EVENT = "EVENT"
    LOCATION = "LOCATION"
    DATE = "DATE"
    UNKNOWN = "UNKNOWN"

class NextStep(str, Enum):
    """Next step in the workflow."""
    NARRATIVE = "narrative"
    CRYPTO = "crypto"
    GENERAL = "general"
    ERROR = "error"
    END = "end"

# Rest of the file remains the same
