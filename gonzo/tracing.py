"""LangSmith tracing setup for Gonzo."""
import os
from typing import Optional, Dict, Any
from langsmith import Client
from langsmith.run_trees import RunTree

def init_tracing(project_name: str = "gonzo-langgraph") -> None:
    """Initialize LangSmith tracing."""
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
    os.environ["LANGCHAIN_PROJECT"] = project_name

def create_run_tree(name: str, metadata: Optional[Dict[str, Any]] = None) -> RunTree:
    """Create a run tree for tracing a specific operation."""
    client = Client()
    return client.create_run_tree(
        name=name,
        project_name=os.getenv("LANGCHAIN_PROJECT", "gonzo-langgraph"),
        metadata=metadata or {}
    )