#!/usr/bin/env python3

import os
import logging
import asyncio
from typing import Dict, Any, Tuple
from datetime import datetime
from dotenv import load_dotenv

from gonzo.state_management import WorkflowStage, create_empty_graph_state, GonzoGraphState
from gonzo.graph.workflow import create_workflow
from gonzo.tracing import init_tracing, TraceManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def init_environment() -> None:
    """Initialize environment variables and tracing."""
    load_dotenv()
    
    # Required API keys for MVP
    required_vars = [
        'ANTHROPIC_API_KEY',  # For analysis/commentary
        'BRAVE_API_KEY',      # For news monitoring
    ]
    
    # Optional API keys
    optional_vars = [
        'LANGCHAIN_API_KEY'   # For tracing
    ]
    
    # Check required variables
    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        raise ValueError(f'Missing required environment variables: {missing}')
        
    # Check optional variables
    missing_optional = [var for var in optional_vars if not os.getenv(var)]
    if missing_optional:
        logger.warning(f'Missing optional variables (some features disabled): {missing_optional}')
    else:
        # Only initialize tracing if we have the API key
        init_tracing()

def get_thread_id() -> str:
    """Create a unique thread ID for state persistence."""
    return f"gonzo_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

async def run_workflow_cycle(workflow, memory, initial_state: GonzoGraphState) -> Tuple[GonzoGraphState, bool]:
    """Run a single workflow cycle with optional tracing."""
    tracer = TraceManager()
    run_id = None
    thread_id = get_thread_id()
    
    try:
        # Start trace if tracing is enabled
        if tracer.enabled:
            run_id = tracer.start_trace(
                "gonzo_workflow_cycle",
                metadata={
                    "timestamp": datetime.now().isoformat(),
                    "initial_stage": initial_state.get('current_stage', WorkflowStage.MONITORING.value)
                }
            )
        
        # Compile with simple config like the example
        graph = workflow.compile(checkpointer=memory)
        config = {"configurable": {"thread_id": thread_id}}
        
        # Stream through workflow states
        current_state = await graph.ainvoke(initial_state, config)
        
        # Log final state
        logger.info(
            f"Stage: {current_state.get('current_stage')}, "
            f"Events: {len(current_state.get('events', []))}, "
            f"Patterns: {len(current_state.get('patterns', []))}, "
            f"Insights: {len(current_state.get('insights', []))}"
        )
        
        return current_state, True
        
    except Exception as e:
        logger.error(f'Error in workflow cycle: {str(e)}')
        if run_id:
            tracer.update_trace(run_id, {"error": str(e)})
            tracer.end_trace(run_id)
        return initial_state, False

async def run_gonzo_async():
    """Async main execution function for Gonzo"""
    try:
        # Initialize environment
        init_environment()
        logger.info('Environment initialized')
        
        # Create initial state
        initial_state = create_empty_graph_state()
        logger.info('Initial state created')
        
        # Create workflow
        workflow, memory = create_workflow()
        logger.info('Workflow created, starting Gonzo...')
        
        # Run workflow
        new_state, completed = await run_workflow_cycle(workflow, memory, initial_state)
        
        if completed:
            logger.info(
                f'Workflow completed successfully with '
                f"{len(new_state.get('events', []))} events, "
                f"{len(new_state.get('patterns', []))} patterns, and "
                f"{len(new_state.get('insights', []))} insights"
            )
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