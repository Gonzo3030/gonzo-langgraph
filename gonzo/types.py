from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class Message(BaseModel):
    """Represents a message in the system."""
    content: str
    timestamp: datetime = datetime.now()
    metadata: Optional[dict] = None