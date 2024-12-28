"""LangSmith tracing setup for Gonzo."""
import os
from typing import Optional, Dict, Any
from langsmith import Client

def init_tracing(project_name: str = "gonzo-langgraph") -> None:
    """Initialize LangSmith tracing."""
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
    os.environ["LANGCHAIN_PROJECT"] = project_name

class TraceManager:
    """Manages LangSmith tracing for Gonzo."""
    
    def __init__(self):
        self.client = Client()
        self.project = os.getenv("LANGCHAIN_PROJECT", "gonzo-langgraph")
    
    def start_trace(self, name: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Start a new trace."""
        run = self.client.create_run(
            name=name,
            inputs={},
            run_type="chain",
            project_name=self.project,
            extra={"metadata": metadata or {}}
        )
        return run.id
    
    def update_trace(self, run_id: str, metadata: Dict[str, Any]) -> None:
        """Update trace metadata."""
        self.client.update_run(
            run_id,
            extra={"metadata": metadata}
        )
    
    def end_trace(self, run_id: str, outputs: Optional[Dict[str, Any]] = None) -> None:
        """End a trace with optional outputs."""
        self.client.update_run(
            run_id,
            outputs=outputs or {},
            end_time=None  # Will use current time
        )
