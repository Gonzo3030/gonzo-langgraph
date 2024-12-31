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
runner = None

def handle_sigint(signum, frame):
    """Handle SIGINT (Ctrl+C) more gracefully."""
    global shutdown_flag, runner
    if shutdown_flag:  # If flag is already set, force exit
        logger.info('Forced shutdown...')
        if runner:
            asyncio.create_task(runner.stop(force=True))
        sys.exit(1)
    else:
        shutdown_flag = True
        logger.info('Graceful shutdown initiated... (Ctrl+C again to force)')
        if runner:
            asyncio.create_task(runner.stop())

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

class PublisherRunner:
    """Manages continuous publishing operation."""
    
    def __init__(self):
        self.running = False
        self.current_workflow = None
        
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
                    # Create new workflow for each cycle
                    workflow, memory = create_publish_workflow()
                    self.current_workflow = workflow
                    
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
                    if not shutdown_flag:  # Only save if not shutting down
                        state_store.save_state(current_state)
                        
                        logger.info(
                            f"Published posts: {len(current_state.get('published_posts', []))}, "
                            f"Remaining in queue: {len(current_state.get('queued_posts', []))}"
                        )
                    
                    if shutdown_flag:
                        break
                        
                except asyncio.CancelledError:
                    logger.info('Workflow cancelled')
                    break
                except Exception as e:
                    logger.error(f'Error in publish cycle: {str(e)}')
                    if shutdown_flag:
                        break
                
                # Check queue every minute
                if not shutdown_flag:
                    try:
                        for _ in range(60):  # Check shutdown flag every second
                            if shutdown_flag:
                                break
                            await asyncio.sleep(1)
                    except asyncio.CancelledError:
                        break
                
        except Exception as e:
            logger.error(f'Failed to run publisher: {str(e)}')
            raise
            
        finally:
            self.running = False
            logger.info('Publisher stopped')
    
    async def stop(self, force: bool = False):
        """Stop the publisher gracefully."""
        if self.current_workflow:
            # Cancel current workflow
            try:
                # Attempt to cancel any running tasks
                tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
                for task in tasks:
                    task.cancel()
                if tasks:
                    await asyncio.gather(*tasks, return_exceptions=True)
            except Exception as e:
                logger.error(f"Error stopping workflow: {e}")

def run_publisher():
    """Main execution function"""
    global runner
    
    # Setup SIGINT handler
    signal.signal(signal.SIGINT, handle_sigint)
    
    runner = PublisherRunner()
    try:
        asyncio.run(runner.start())
    except KeyboardInterrupt:
        logger.info('Caught KeyboardInterrupt in main')

if __name__ == '__main__':
    run_publisher()