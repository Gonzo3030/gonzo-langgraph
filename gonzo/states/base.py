from typing import Dict, Any
from abc import ABC, abstractmethod

class BaseState(ABC):
    """Base class for all Gonzo agent states."""
    
    @abstractmethod
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Run the state's logic and return updated state."""
        pass
    
    def validate_state(self, state: Dict[str, Any]) -> bool:
        """Validate the current state."""
        return True
    
    def get_required_tools(self) -> list:
        """Get list of required tools for this state."""
        return []
    
    def get_required_memory(self) -> list:
        """Get list of required memory components."""
        return []
    
    def cleanup(self) -> None:
        """Cleanup any resources used by the state."""
        pass