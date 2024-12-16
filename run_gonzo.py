#!/usr/bin/env python3

import os
import logging
from dotenv import load_dotenv
from gonzo.types import create_initial_state
from gonzo.workflow import create_workflow

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def init_environment():
    """Initialize environment variables"""
    load_dotenv()
    required_vars = [
        'ANTHROPIC_API_KEY',
        'OPENAI_API_KEY',
        'BRAVE_API_KEY',
        'LANGCHAIN_API_KEY',
        'CRYPTOCOMPARE_API_KEY',
        'YOUTUBE_API_KEY',
        'X_API_KEY',
        'X_API_SECRET',
        'X_ACCESS_TOKEN',
        'X_ACCESS_SECRET'
    ]
    
    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        raise ValueError(f'Missing required environment variables: {missing}')

def main():
    try:
        # Initialize environment
        init_environment()
        logger.info('Environment initialized')
        
        # Create initial state
        state = create_initial_state()
        logger.info('Initial state created')
        
        # Create and start workflow
        workflow = create_workflow()
        logger.info('Workflow created, starting Gonzo...')
        
        # Run the workflow
        workflow.run(state)
        
    except KeyboardInterrupt:
        logger.info('Shutting down Gonzo gracefully...')
    except Exception as e:
        logger.error(f'Failed to start Gonzo: {str(e)}')
        raise

if __name__ == '__main__':
    main()
