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
    
    # Required API keys for MVP
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
    
    # Set defaults for optional LangChain variables
    os.environ.setdefault('LANGCHAIN_TRACING_V2', 'true')
    os.environ.setdefault('LANGCHAIN_ENDPOINT', 'https://api.smith.langchain.com')
    os.environ.setdefault('LANGCHAIN_PROJECT', 'gonzo-langgraph')

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
        
        # Run the workflow with initial state
        workflow.invoke({"messages": [], "next": "detect"})
        logger.info('Gonzo is running!')
        
        # Keep the workflow running
        while True:
            try:
                # Keep monitoring and processing
                workflow.invoke({"messages": state["messages"], "next": "detect"})
            except KeyboardInterrupt:
                logger.info('\nShutting down Gonzo gracefully...')
                break
            except Exception as e:
                logger.error(f'Error in workflow cycle: {str(e)}')
                # Continue running despite errors
                continue
        
    except KeyboardInterrupt:
        logger.info('Shutting down Gonzo gracefully...')
    except Exception as e:
        logger.error(f'Failed to start Gonzo: {str(e)}')
        raise

if __name__ == '__main__':
    main()