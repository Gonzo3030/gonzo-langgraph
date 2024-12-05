from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
from datetime import datetime
from .mixins import LangSmithTracking
from ..tools.batch_processing import BatchProcessor

class BaseState(ABC, LangSmithTracking):
    """Enhanced base class for all Gonzo agent states with LangSmith tracking."""
    
    def __init__(self):
        super().__init__()
        self.batch_processor: Optional[BatchProcessor] = None
    
    @abstractmethod
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Run the state's logic and return updated state."""
        pass
    
    def validate_state(self, state: Dict[str, Any]) -> bool:
        """Validate the current state."""
        with self.track_run('validate_state'):
            return True
    
    def get_required_tools(self) -> list:
        """Get list of required tools for this state."""
        return []
    
    def get_required_memory(self) -> list:
        """Get list of required memory components."""
        return []
    
    def save_to_memory(self, state: Dict[str, Any], key: str, value: Any) -> None:
        """Save data to state memory with timestamp."""
        with self.track_run('save_to_memory') as run:
            state['memory'] = state.get('memory', {})
            state['memory'][key] = {
                'value': value,
                'timestamp': datetime.now().isoformat()
            }
            run.update_outputs({'key': key, 'timestamp': state['memory'][key]['timestamp']})
    
    def initialize_batch_processor(self, run_tree=None) -> None:
        """Initialize the batch processor for this state."""
        if not self.batch_processor:
            self.batch_processor = BatchProcessor(run_tree=run_tree)
    
    async def process_events(self, events: list, category: str) -> Dict[str, Any]:
        """Process a list of events using the batch processor."""
        with self.track_run('process_events') as run:
            if not self.batch_processor:
                self.initialize_batch_processor(run_tree=run)
                
            for event in events:
                await self.batch_processor.add_event(event, category)
                
            batch = await self.batch_processor.process_batch(category)
            return batch.dict() if batch else {}
    
    def cleanup(self) -> None:
        """Cleanup any resources used by the state."""
        self.batch_processor = None