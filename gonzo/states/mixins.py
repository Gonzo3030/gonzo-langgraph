from typing import Dict, Any, Optional
from langsmith.run_trees import RunTree

class LangSmithTracking:
    """Mixin to add LangSmith tracking capabilities to states."""
    
    def __init__(self):
        self._run_tree: Optional[RunTree] = None
        
    def set_run_tree(self, run_tree: RunTree) -> None:
        """Set the LangSmith run tree for tracking."""
        self._run_tree = run_tree
        
    def track_run(self, name: str):
        """Context manager for tracking a run."""
        if self._run_tree:
            return self._run_tree.as_child(name)
        return nullcontext()
        
    def log_step(self, name: str, inputs: Dict[str, Any], outputs: Dict[str, Any]) -> None:
        """Log a step within the current run."""
        if self._run_tree:
            with self._run_tree.as_child(name) as run:
                run.update_inputs(inputs)
                run.update_outputs(outputs)
                
    def on_error(self, error: Exception) -> None:
        """Log an error in the current run."""
        if self._run_tree:
            self._run_tree.on_error(str(error))
            
    def update_metrics(self, metrics: Dict[str, Any]) -> None:
        """Update run metrics."""
        if self._run_tree:
            self._run_tree.update_outputs(metrics)

from contextlib import contextmanager, nullcontext