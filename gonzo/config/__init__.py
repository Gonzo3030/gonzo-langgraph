"""Configuration management for Gonzo system."""

from .models import MODEL_NAME, MODEL_CONFIG, GRAPH_CONFIG
from .analysis import ANALYSIS_CONFIG
from .prompts import SYSTEM_PROMPT, ANALYSIS_PROMPT_TEMPLATE, RESPONSE_PROMPT_TEMPLATE
from .tasks import TASK_PROMPTS, TASK_CONFIG
from .constants import *

__all__ = [
    'MODEL_NAME',
    'MODEL_CONFIG',
    'GRAPH_CONFIG',
    'ANALYSIS_CONFIG',
    'SYSTEM_PROMPT',
    'ANALYSIS_PROMPT_TEMPLATE',
    'RESPONSE_PROMPT_TEMPLATE',
    'TASK_PROMPTS',
    'TASK_CONFIG'
]