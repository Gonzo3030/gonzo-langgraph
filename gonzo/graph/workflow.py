"""Core workflow definition for Gonzo system."""

from typing import Dict, Any, Optional
from datetime import datetime
from langchain_core.language_models import BaseLLM
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, END

from ..config import MODEL_CONFIG, GRAPH_CONFIG, SYSTEM_PROMPT
from ..state_management import (
    UnifiedState,
    WorkflowStage,
    create_initial_state
)
from ..nodes.initial_assessment import initial_assessment
from ..nodes.pattern_detection import detect_patterns
from ..nodes.response_generation import generate_response
from ..monitoring.news_monitor import NewsMonitor

# Rest of the file remains the same...