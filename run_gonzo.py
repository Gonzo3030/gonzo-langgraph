#!/usr/bin/env python3

import os
import logging
import asyncio
from typing import Dict, Any, Tuple
from datetime import datetime
from dotenv import load_dotenv

from gonzo.state_management import GonzoState, create_initial_state, WorkflowStage
from gonzo.graph.workflow import create_workflow, ensure_state
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

async def run_workflow_cycle(app, current_state: Dict) -> Tuple[Dict, bool]:
    """Run a single workflow cycle with optional tracing."""
    tracer = TraceManager()
    run_id = None
    
    try:
        # Start trace if tracing is enabled
        if tracer.enabled:
            state_obj = ensure_state(current_state)
            run_id = tracer.start_trace(
                "gonzo_workflow_cycle",
                metadata={
                    "timestamp": datetime.now().isoformat(),
                    "initial_stage": state_obj.current_stage.value
                }
            )
        
        async for output in app.astream(current_state):
            if output is None:
                continue
            
            # Extract new state, converting current_stage to enum
            current_stage = (
                WorkflowStage(output["current_stage"])
                if output.get("current_stage")
                else WorkflowStage.MONITORING
            )
            
            state_obj = GonzoState(
                events=output.get("events", []),
                patterns=output.get("patterns", []),
                insights=output.get("insights", []),
                current_stage=current_stage,
                errors=output.get("errors", [])
            )
            
            # Log progress
            logger.info(
                f"Stage: {state_obj.current_stage}, "
                f"Events: {len(state_obj.events)}, "
                f"Patterns: {len(state_obj.patterns)}, "
                f"Insights: {len(state_obj.insights)}"
            )
            
            # Update trace if enabled
            if run_id:
                tracer.update_trace(run_id, {
                    "final_stage": state_obj.current_stage.value,
                    "events_found": len(state_obj.events),
                    "patterns_found": len(state_obj.patterns),
                    "insights_generated": len(state_obj.insights)
                })
            
            # Return the state dictionary
            return output, True
        
        return current_state, False
        
    except Exception as e:
        logger.error(f'Error in workflow cycle: {str(e)}')
        if run_id:
            tracer.update_trace(run_id, {"error": str(e)})
            tracer.end_trace(run_id)
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
        
        # Run workflow with unpacked state
        current_state = {
            "events": state.events,
            "patterns": state.patterns,
            "insights": state.insights,
            "current_stage": state.current_stage.value,  # Convert enum to string
            "errors": state.errors
        }
        
        new_state, completed = await run_workflow_cycle(app, current_state)
        
        # Convert current_stage back to enum
        current_stage = (
            WorkflowStage(new_state["current_stage"])
            if new_state.get("current_stage")
            else WorkflowStage.MONITORING
        )
        
        final_state = GonzoState(
            events=new_state.get("events", []),
            patterns=new_state.get("patterns", []),
            insights=new_state.get("insights", []),
            current_stage=current_stage,
            errors=new_state.get("errors", [])
        )
        
        if completed:
            logger.info(
                f'Workflow completed successfully with {len(final_state.events)} events, '
                f'{len(final_state.patterns)} patterns, and '
                f'{len(final_state.insights)} insights'
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