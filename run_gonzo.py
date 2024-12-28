#!/usr/bin/env python3

import os
import logging
import asyncio
from typing import Dict, Any, Tuple
from datetime import datetime
from dotenv import load_dotenv

from gonzo.state_management import GonzoState, create_initial_state
from gonzo.graph.workflow import create_workflow

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def init_environment() -> None:
    """Initialize environment variables"""
    load_dotenv()
    
    # Required API keys for MVP
    required_vars = [
        'ANTHROPIC_API_KEY',  # For analysis/commentary
        'BRAVE_API_KEY',      # For news monitoring
    ]
    
    # Check required variables
    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        raise ValueError(f'Missing required environment variables: {missing}')

async def run_workflow_cycle(app, current_state) -> Tuple[Dict, bool]:
    """Run a single workflow cycle"""
    try:
        async for output in app.astream(current_state):
            if output is None:
                continue
            
            # Extract new state
            new_state = GonzoState(**output)
            
            # Log progress
            logger.info(
                f"Stage: {new_state.current_stage}, "
                f"Events: {len(new_state.events)}, "
                f"Patterns: {len(new_state.patterns)}, "
                f"Insights: {len(new_state.insights)}"
            )
            
            return new_state.model_dump(), True
        
        return current_state, False
        
    except Exception as e:
        logger.error(f'Error in workflow cycle: {str(e)}')
        return current_state, False

async def run_gonzo_async():
    """Async main execution function for Gonzo"""
    try:
        # Initialize environment
        init_environment()
        logger.info('Environment initialized')
        
        # Create initial state
        state = create_initial_state()
        logger.info('Initial state created')
        
        # Create and compile workflow
        workflow = create_workflow()
        app = workflow.compile()
        logger.info('Workflow compiled, starting Gonzo...')
        
        # Run workflow
        current_state = state.model_dump()
        
        new_state, completed = await run_workflow_cycle(app, current_state)
        
        if completed:
            logger.info('Workflow completed successfully')
        else:
            logger.warning('Workflow ended without completion')
            
    except KeyboardInterrupt:
        logger.info('Shutting down Gonzo gracefully...')
    except Exception as e:
        logger.error(f'Failed to run Gonzo: {str(e)}')
        raise

def run_gonzo():
    """Main execution function"""
    asyncio.run(run_gonzo_async())

if __name__ == '__main__':
    run_gonzo()