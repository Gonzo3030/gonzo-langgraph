#!/usr/bin/env python3

import os
import logging
from typing import Dict, Any
from datetime import datetime
from dotenv import load_dotenv

from gonzo.state_management import UnifiedState, create_initial_state, WorkflowStage
from gonzo.graph.workflow import create_workflow
from gonzo.config import SYSTEM_PROMPT

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def init_environment() -> None:
    """Initialize environment variables"""
    load_dotenv()
    
    # Required API keys
    required_vars = [
        'ANTHROPIC_API_KEY',
        'OPENAI_API_KEY',
        'X_API_KEY',
        'X_API_SECRET',
        'X_ACCESS_TOKEN',
        'X_ACCESS_SECRET',
        'BRAVE_API_KEY',  # For market and news monitoring
        'CRYPTOCOMPARE_API_KEY'  # For crypto market data
    ]
    
    # Optional but recommended APIs
    optional_vars = [
        'LANGCHAIN_API_KEY',
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

def setup_initial_state() -> UnifiedState:
    """Create initial state with proper configuration"""
    state = create_initial_state()
    
    # Add system prompt to establish Gonzo's persona
    state.add_message(SYSTEM_PROMPT, source="system")
    
    # Configure X integration
    state.x_integration.direct_api.update({
        'api_key': os.getenv('X_API_KEY'),
        'api_secret': os.getenv('X_API_SECRET'),
        'access_token': os.getenv('X_ACCESS_TOKEN'),
        'access_secret': os.getenv('X_ACCESS_SECRET')
    })
    
    # Store API keys in memory for various services
    state.memory.store(
        "api_credentials",
        {
            'brave_key': os.getenv('BRAVE_API_KEY'),
            'crypto_compare_key': os.getenv('CRYPTOCOMPARE_API_KEY')
        },
        "long_term"
    )
    
    return state

def run_gonzo() -> None:
    """Main execution function for Gonzo"""
    try:
        # Initialize environment
        init_environment()
        logger.info('Environment initialized')
        
        # Create initial state
        state = setup_initial_state()
        logger.info('Initial state created')
        
        # Create workflow
        workflow = create_workflow()
        logger.info('Workflow created, starting Gonzo...')
        
        # Initial run with state dump
        current_state = state.model_dump()
        
        # Keep the workflow running
        while True:
            try:
                # Run workflow cycle
                result = workflow.invoke(current_state)
                
                # Extract new state
                new_state = UnifiedState(**result["state"])
                
                # Log progress
                logger.info(
                    f"Completed cycle. Stage: {new_state.current_stage}, "
                    f"Patterns detected: {len(new_state.knowledge_graph.patterns)}, "
                    f"Queued posts: {len(new_state.x_integration.queued_posts)}"
                )
                
                # Update current state
                current_state = new_state.model_dump()
                
                # Handle checkpointing if needed
                if new_state.checkpoint_needed:
                    # TODO: Implement checkpoint saving
                    pass
                    
            except KeyboardInterrupt:
                logger.info('\nShutting down Gonzo gracefully...')
                break
            except Exception as e:
                logger.error(f'Error in workflow cycle: {str(e)}')
                # Continue to next cycle rather than crashing
                continue
        
    except KeyboardInterrupt:
        logger.info('Shutting down Gonzo gracefully...')
    except Exception as e:
        logger.error(f'Failed to start Gonzo: {str(e)}')
        raise

if __name__ == '__main__':
    run_gonzo()