#!/usr/bin/env python3

import os
import logging
import asyncio
from typing import Dict, Any
from datetime import datetime
from dotenv import load_dotenv

from gonzo.extended_state_management import UnifiedState, create_initial_state
from gonzo.gonzo_workflow import create_workflow, WorkflowStage

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def init_environment() -> None:
    """Initialize environment variables and API keys"""
    load_dotenv()
    
    # Required API keys
    required_vars = [
        'ANTHROPIC_API_KEY',
        'OPENAI_API_KEY',
        'X_API_KEY',
        'X_API_SECRET',
        'X_ACCESS_TOKEN',
        'X_ACCESS_SECRET'
    ]
    
    # Optional API keys
    optional_vars = [
        'BRAVE_API_KEY',
        'LANGCHAIN_API_KEY',
        'CRYPTOCOMPARE_API_KEY',
        'YOUTUBE_API_KEY'
    ]
    
    # Check required variables
    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        raise ValueError(f'Missing required environment variables: {missing}')
    
    # Log warning for missing optional variables
    missing_optional = [var for var in optional_vars if not os.getenv(var)]
    if missing_optional:
        logger.warning(f'Missing optional API keys (some features will be disabled): {missing_optional}')
    
    # Set up LangChain monitoring
    os.environ.setdefault('LANGCHAIN_TRACING_V2', 'true')
    os.environ.setdefault('LANGCHAIN_ENDPOINT', 'https://api.smith.langchain.com')
    os.environ.setdefault('LANGCHAIN_PROJECT', 'gonzo-langgraph')

def setup_x_credentials(state: UnifiedState) -> None:
    """Configure X API credentials in state"""
    state.x_integration.direct_api.update({
        'api_key': os.getenv('X_API_KEY'),
        'api_secret': os.getenv('X_API_SECRET'),
        'access_token': os.getenv('X_ACCESS_TOKEN'),
        'access_secret': os.getenv('X_ACCESS_SECRET')
    })
    
    # Store backup in long-term memory
    state.memory.long_term.update({
        'x_credentials': {
            'api_key': os.getenv('X_API_KEY'),
            'api_secret': os.getenv('X_API_SECRET'),
            'access_token': os.getenv('X_ACCESS_TOKEN'),
            'access_secret': os.getenv('X_ACCESS_SECRET')
        }
    })

def initialize_state() -> UnifiedState:
    """Create and initialize the unified state"""
    state = create_initial_state()
    
    # Set up X credentials
    setup_x_credentials(state)
    
    # Initialize with a test message
    state.add_message(
        "The crypto markets are buzzing with manipulation again. "
        "Every screen flashes green while shadows dance behind the charts.",
        source="test"
    )
    
    return state

async def run_workflow_cycle(workflow: Any, state: Dict[str, Any]) -> Dict[str, Any]:
    """Run a single workflow cycle with proper error handling"""
    try:
        result = workflow.invoke(state)
        
        # Check for critical errors
        if result.get("current_stage") == WorkflowStage.ERROR:
            logger.error(f"Workflow error: {result.get('last_error', 'Unknown error')}")
            # Implement recovery logic here if needed
            
        return result
    except Exception as e:
        logger.error(f"Cycle error: {str(e)}")
        return {
            "current_stage": WorkflowStage.ERROR,
            "last_error": str(e)
        }

async def main_loop() -> None:
    """Main execution loop"""
    try:
        # Initialize environment
        init_environment()
        logger.info('Environment initialized')
        
        # Create initial state
        initial_state = initialize_state()
        logger.info('Initial state created')
        
        # Create workflow
        workflow = create_workflow()
        logger.info('Workflow created, starting Gonzo...')
        
        # Initial state dump
        current_state = initial_state.model_dump()
        
        # Main loop
        while True:
            try:
                # Run workflow cycle
                result = await run_workflow_cycle(workflow, current_state)
                
                # Update current state
                current_state = result
                
                # Log progress
                logger.info(f"Completed cycle. Stage: {result.get('current_stage', 'unknown')}")
                
                # Optional: Add delay between cycles
                await asyncio.sleep(1)
                
            except KeyboardInterrupt:
                logger.info('\nShutting down Gonzo gracefully...')
                break
            except Exception as e:
                logger.error(f'Error in workflow cycle: {str(e)}')
                # Implement recovery or continue based on error
                continue
    
    except KeyboardInterrupt:
        logger.info('Shutting down Gonzo gracefully...')
    except Exception as e:
        logger.error(f'Failed to start Gonzo: {str(e)}')
        raise

def main():
    """Entry point"""
    try:
        asyncio.run(main_loop())
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        raise

if __name__ == '__main__':
    main()
