"""LangSmith tracing setup for Gonzo."""
import os
import logging
from typing import Optional, Dict, Any
from langsmith import Client

logger = logging.getLogger(__name__)

def init_tracing(project_name: str = "gonzo-langgraph") -> None:
    """Initialize LangSmith tracing."""
    try:
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
        os.environ["LANGCHAIN_PROJECT"] = project_name
        logger.info("LangSmith tracing initialized")
    except Exception as e:
        logger.error(f"Failed to initialize tracing: {str(e)}")
        raise

class TraceManager:
    """Manages LangSmith tracing for Gonzo."""
    
    def __init__(self):
        self.enabled = False
        try:
            self.client = Client()
            self.project = os.getenv("LANGCHAIN_PROJECT", "gonzo-langgraph")
            logger.info(f"TraceManager initialized for project: {self.project}")
            self.enabled = True
        except Exception as e:
            logger.error(f"Failed to initialize TraceManager: {str(e)}")
    
    def start_trace(self, name: str, metadata: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Start a new trace."""
        if not self.enabled:
            logger.warning("Tracing is disabled - skipping trace start")
            return None
            
        try:
            logger.info(f"Starting trace: {name}")
            run = self.client.create_run(
                name=name,
                inputs={},
                run_type="chain",
                project_name=self.project,
                extra={"metadata": metadata or {}}
            )
            if not run or not hasattr(run, 'id'):
                logger.error("Failed to create run - no run ID returned")
                return None
            logger.info(f"Started trace with ID: {run.id}")
            return run.id
        except Exception as e:
            logger.error(f"Error starting trace: {str(e)}")
            return None
    
    def update_trace(self, run_id: Optional[str], metadata: Dict[str, Any]) -> None:
        """Update trace metadata."""
        if not self.enabled or not run_id:
            return
            
        try:
            logger.debug(f"Updating trace {run_id} with metadata: {metadata}")
            self.client.update_run(
                run_id,
                extra={"metadata": metadata}
            )
        except Exception as e:
            logger.error(f"Error updating trace: {str(e)}")
    
    def end_trace(self, run_id: Optional[str], outputs: Optional[Dict[str, Any]] = None) -> None:
        """End a trace with optional outputs."""
        if not self.enabled or not run_id:
            return
            
        try:
            logger.info(f"Ending trace: {run_id}")
            self.client.update_run(
                run_id,
                outputs=outputs or {},
                end_time=None  # Will use current time
            )
        except Exception as e:
            logger.error(f"Error ending trace: {str(e)}")
