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

# Global shutdown flag
shutdown_flag = False

def handle_sigint(signum, frame):
    """Handle SIGINT (Ctrl+C) more aggressively."""
    global shutdown_flag
    if shutdown_flag:  # If flag is already set, force exit
        logger.info('Forced shutdown...')
        sys.exit(1)
    else:
        shutdown_flag = True
        logger.info('Graceful shutdown initiated... (Ctrl+C again to force)')

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
        # Check shutdown flag
        if shutdown_flag:
            return None
            
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
        
    async def start(self):
        """Start continuous publishing operation."""
        try:
            # Initialize environment
            init_environment()
            logger.info('Environment initialized')
            
            self.running = True
            
            logger.info('Starting publisher...')
            
            while not shutdown_flag:
                try:
                    await run_publish_cycle()
                    if shutdown_flag:
                        break
                except Exception as e:
                    logger.error(f'Error in publish cycle: {str(e)}')
                    if shutdown_flag:
                        break
                
                # Check queue every minute
                for _ in range(60):  # Check shutdown flag every second
                    if shutdown_flag:
                        break
                    await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f'Failed to run publisher: {str(e)}')
            raise
            
        finally:
            self.running = False
            logger.info('Publisher stopped')

def run_publisher():
    """Main execution function"""
    # Setup SIGINT handler
    signal.signal(signal.SIGINT, handle_sigint)
    
    runner = PublisherRunner()
    try:
        asyncio.run(runner.start())
    except KeyboardInterrupt:
        logger.info('Caught KeyboardInterrupt in main')

if __name__ == '__main__':
    run_publisher()