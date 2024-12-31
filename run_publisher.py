#!/usr/bin/env python3

import os
import sys
import signal
import logging
import asyncio
from typing import Dict, Any
from datetime import datetime
from dotenv import load_dotenv

from gonzo.state_management import WorkflowStage, create_empty_graph_state
from gonzo.state_management.storage import GonzoStateStore
from gonzo.graph.publish_workflow import create_publish_workflow
from gonzo.tracing import init_tracing

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize state store
state_store = GonzoStateStore()

def init_environment() -> None:
    """Initialize environment variables and tracing."""
    load_dotenv()
    
    # Required API keys
    required_vars = [
        'X_API_KEY',       # For Twitter posting
        'X_API_SECRET',
        'X_ACCESS_TOKEN',
        'X_ACCESS_SECRET'
    ]
    
    # Check required variables
    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        raise ValueError(f'Missing required environment variables: {missing}')
        
    # Initialize tracing if available
    if os.getenv('LANGCHAIN_API_KEY'):
        init_tracing()

async def run_publish_cycle():
    """Run a single publishing cycle."""
    try:
        # Create workflow
        workflow, memory = create_publish_workflow()
        
        # Load state from storage
        stored_state = state_store.load_state()
        if stored_state:
            logger.info('Retrieved state from storage')
            last_state = stored_state
        else:
            last_state = create_empty_graph_state()
            logger.info('Created new state')
        
        # Run workflow
        graph = workflow.compile(checkpointer=memory)
        config = {"configurable": {"thread_id": f"publisher_{datetime.now().strftime('%Y%m%d_%H%M%S')}"}}        
        
        current_state = await graph.ainvoke(last_state, config)
        
        # Save updated state
        state_store.save_state(current_state)
        
        logger.info(
            f"Published posts: {len(current_state.get('published_posts', []))}, "
            f"Remaining in queue: {len(current_state.get('queued_posts', []))}"
        )
        
        return current_state
        
    except Exception as e:
        logger.error(f'Error in publish cycle: {str(e)}')
        return None

class PublisherRunner:
    """Manages continuous publishing operation."""
    
    def __init__(self):
        self.running = False
        self._shutdown = False
    
    async def shutdown(self, sig=None):
        """Handle graceful shutdown."""
        if sig:
            logger.info(f'Received exit signal {sig.name}...')
            
        self._shutdown = True
        logger.info('Waiting for current cycle to complete...')
        
        while self.running:
            await asyncio.sleep(1)
            
        logger.info('Shutdown complete')
    
    async def start(self):
        """Start continuous publishing operation."""
        try:
            # Initialize environment
            init_environment()
            logger.info('Environment initialized')
            
            self.running = True
            self._shutdown = False
            
            # Setup signal handlers
            for sig in (signal.SIGTERM, signal.SIGINT):
                asyncio.get_event_loop().add_signal_handler(
                    sig,
                    lambda s=sig: asyncio.create_task(self.shutdown(s))
                )
            
            logger.info('Starting publisher...')
            
            while not self._shutdown:
                try:
                    await run_publish_cycle()
                except Exception as e:
                    logger.error(f'Error in publish cycle: {str(e)}')
                
                # Check queue every minute
                await asyncio.sleep(60)
                
        except Exception as e:
            logger.error(f'Failed to run publisher: {str(e)}')
            raise
            
        finally:
            self.running = False

def run_publisher():
    """Main execution function"""
    runner = PublisherRunner()
    asyncio.run(runner.start())

if __name__ == '__main__':
    run_publisher()