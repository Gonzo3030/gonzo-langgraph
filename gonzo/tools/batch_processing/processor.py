from typing import List, Dict, Any
from dataclasses import dataclass
from collections import defaultdict
import asyncio
from langsmith.run_trees import RunTree
from .embeddings import EmbeddingProcessor

@dataclass
class EventBatch:
    """Represents a batch of processed events."""
    events: List[Dict[Any, Any]]
    batch_id: str
    checkpoint_id: str
    similarity_score: float

    def dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            'events': self.events,
            'batch_id': self.batch_id,
            'checkpoint_id': self.checkpoint_id,
            'similarity_score': self.similarity_score
        }

class BatchProcessor:
    """Processes events in batches with semantic grouping and LangSmith tracking."""
    
    def __init__(self, 
                 batch_size: int = 5,
                 similarity_threshold: float = 0.8,
                 max_batch_wait: int = 60,
                 run_tree: RunTree = None):
        self.batch_size = batch_size
        self.similarity_threshold = similarity_threshold
        self.max_batch_wait = max_batch_wait
        self.pending_events = defaultdict(list)
        self.embedding_processor = EmbeddingProcessor(run_tree)
        self.run_tree = run_tree
        
    async def add_event(self, event: Dict[Any, Any], category: str) -> None:
        """Add an event to the pending batch for a given category."""
        if self.run_tree:
            with self.run_tree.as_child('add_event'):
                await self._add_event(event, category)
        else:
            await self._add_event(event, category)
            
    async def _add_event(self, event: Dict[Any, Any], category: str) -> None:
        """Internal method for adding events."""
        self.pending_events[category].append(event)
        
        if len(self.pending_events[category]) >= self.batch_size:
            await self.process_batch(category)
            
    async def process_batch(self, category: str) -> EventBatch:
        """Process a batch of events in the same category."""
        if not self.pending_events[category]:
            return None
            
        events = self.pending_events[category]
        self.pending_events[category] = []
        
        if self.run_tree:
            with self.run_tree.as_child('process_batch') as run:
                return await self._process_batch_internal(events, category, run)
        else:
            return await self._process_batch_internal(events, category)
            
    async def _process_batch_internal(self, events: List[Dict[Any, Any]], category: str, 
                                     run: RunTree = None) -> EventBatch:
        """Internal batch processing with optional LangSmith tracking."""
        # Process embeddings
        events_with_embeddings = await self.embedding_processor.batch_process_embeddings(events)
        
        # Group similar events
        grouped_events = await self._group_similar_events(events_with_embeddings)
        
        # Create checkpoint
        checkpoint_id = await self._create_checkpoint(grouped_events)
        
        batch = EventBatch(
            events=grouped_events,
            batch_id=f"batch_{category}_{checkpoint_id}",
            checkpoint_id=checkpoint_id,
            similarity_score=await self.embedding_processor.calculate_group_similarity(events)
        )
        
        if run:
            run.update_outputs({
                'batch_size': len(events),
                'groups': len(grouped_events),
                'similarity_score': batch.similarity_score
            })
        
        return batch

    async def _create_checkpoint(self, grouped_events: List[Dict[Any, Any]]) -> str:
        """Create a checkpoint for the batch processing state."""
        checkpoint_id = f"batch_{len(grouped_events)}_{hash(str(grouped_events))}"
        
        if self.run_tree:
            with self.run_tree.as_child('create_checkpoint') as run:
                run.update_outputs({'checkpoint_id': checkpoint_id})
        
        return checkpoint_id
        
    async def monitor_pending_batches(self):
        """Monitor and process batches that exceed wait time."""
        while True:
            current_time = asyncio.get_event_loop().time()
            
            for category, events in self.pending_events.items():
                if events and (current_time - events[0].get("timestamp", 0)) > self.max_batch_wait:
                    await self.process_batch(category)
                    
            await asyncio.sleep(5)