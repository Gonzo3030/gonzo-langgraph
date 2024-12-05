from typing import TypedDict, Optional, Dict, Any
from pydantic import BaseModel  # Updated to use pydantic v2 directly

class GonzoState(TypedDict):
    """Base state class for Gonzo"""
    messages: list[str]
    api_queries: list[str]
    api_responses: Dict[str, Any]
    api_errors: list[str]
    memory: Dict[str, Any]
    next_steps: list[str]

def create_initial_state() -> GonzoState:
    """Create the initial state for Gonzo"""
    return GonzoState(
        messages=[],
        api_queries=[],
        api_responses={},
        api_errors=[],
        memory={},
        next_steps=[]
    )