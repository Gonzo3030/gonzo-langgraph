#!/usr/bin/env python3

import os
import sys
import signal
import logging
import asyncio
from typing import Dict, Any, Tuple, Optional
from datetime import datetime
from dotenv import load_dotenv
import yaml

from gonzo.state_management import WorkflowStage, create_empty_graph_state, GonzoGraphState
from gonzo.graph.workflow import create_workflow
from gonzo.tracing import init_tracing, TraceManager
from gonzo.scheduling import WorkflowScheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_config() -> Dict[str, Any]:
    """Load configuration from config.yml"""
    config_path = os.path.join('config', 'config.yml')
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f'Error loading config: {str(e)}')
        sys.exit(1)

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
        
        # Compile with simple config
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

class GonzoRunner:
    """Manages Gonzo's continuous operation."""
    
    def __init__(self):
        self.scheduler = None
        self.workflow = None
        self.memory = None
        self.current_state = None
        self.config = None
        
    async def shutdown(self, sig=None):
        """Handle graceful shutdown."""
        if sig:
            logger.info(f'Received exit signal {sig.name}...')
        
        if self.scheduler and self.scheduler.is_running:
            logger.info('Initiating graceful shutdown...')
            self.scheduler.request_shutdown()
            
            # Wait for scheduler to complete current cycle
            while self.scheduler.is_running:
                await asyncio.sleep(1)
                
        logger.info('Shutdown complete')
    
    async def run_workflow(self):
        """Run a single workflow cycle."""
        if not self.current_state:
            self.current_state = create_empty_graph_state()
            
        new_state, completed = await run_workflow_cycle(
            self.workflow,
            self.memory,
            self.current_state
        )
        
        if completed:
            self.current_state = new_state
    
    async def start(self):
        """Start Gonzo's continuous operation."""
        try:
            # Initialize environment and load config
            init_environment()
            self.config = load_config()
            logger.info('Environment and configuration initialized')
            
            # Create workflow components
            self.workflow, self.memory = create_workflow()
            self.current_state = create_empty_graph_state()
            logger.info('Workflow components created')
            
            # Initialize scheduler
            self.scheduler = WorkflowScheduler(self.config)
            
            # Setup signal handlers
            for sig in (signal.SIGTERM, signal.SIGINT):
                asyncio.get_event_loop().add_signal_handler(
                    sig,
                    lambda s=sig: asyncio.create_task(self.shutdown(s))
                )
            
            logger.info('Starting Gonzo...')
            await self.scheduler.schedule_workflow(self.run_workflow)
            
        except Exception as e:
            logger.error(f'Failed to run Gonzo: {str(e)}')
            await self.shutdown()
            raise

def run_gonzo():
    """Main execution function"""
    runner = GonzoRunner()
    asyncio.run(runner.start())

if __name__ == '__main__':
    run_gonzo()
