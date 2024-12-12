from enum import Enum

class NextStep(str, Enum):
    """Possible next steps in the workflow"""
    ANALYZE = "analyze"
    EVOLVE = "evolve"
    GENERATE_RESPONSE = "generate_response"
    SEND_RESPONSE = "send_response"
    END = "end"
    ERROR = "error"