"""Simplified workflow implementation for Gonzo MVP."""
import os
import logging
from typing import Dict, Any, Optional, Union, TypedDict, Annotated, Tuple
from datetime import datetime
from operator import itemgetter
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from ..state_management import GonzoState, WorkflowStage, Event
from ..monitoring.brave_monitor import BraveMonitor

logger = logging.getLogger(__name__)

# Define state schema for LangGraph
class GonzoGraphState(TypedDict):
    events: list
    patterns: list
    insights: list
    current_stage: str
    errors: list

def create_empty_state() -> Dict[str, Any]:
    """Create an empty state dictionary with all required fields."""
    return {
        "events": [],
        "patterns": [],
        "insights": [],
        "current_stage": WorkflowStage.MONITORING.value,
        "errors": []
    }

async def monitor_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Monitor for relevant events using Brave API."""
    # Always work with a copy of the state
    current_state = state.copy() if state else create_empty_state()
    logger.info("Starting monitoring phase")
    
    try:
        # Initialize Brave monitor
        api_key = os.getenv('BRAVE_API_KEY')
        if not api_key:
            raise ValueError("BRAVE_API_KEY not found in environment")
            
        monitor = BraveMonitor(api_key)
        logger.info("Initialized Brave monitor")
        
        # Get search queries
        queries = monitor.generate_queries()
        
        # Initialize event collection
        new_events = []
        total_events = 0
        
        # Search for each query
        for query in queries:
            try:
                logger.info(f"Processing query: {query}")
                news_items = await monitor.search_news(query)
                
                # Convert news items to events
                for item in news_items:
                    event = Event(
                        timestamp=datetime.now(),
                        title=item.get('title', ''),
                        content=item.get('description', ''),
                        source=item.get('source', ''),
                        url=item.get('url')
                    )
                    new_events.append(event.model_dump())
                    total_events += 1
                    
            except Exception as e:
                error_msg = f"Error searching {query}: {str(e)}"
                logger.error(error_msg)
                current_state['errors'] = current_state.get('errors', []) + [error_msg]
        
        logger.info(f"Completed monitoring phase. Found {total_events} events")
        
        # Update state with new events
        current_state['events'] = new_events
        
        # Move to analysis stage if we found any events
        if total_events > 0:
            current_state['current_stage'] = WorkflowStage.ANALYSIS.value
            logger.info(f"Moving to ANALYSIS stage with {total_events} events")
        else:
            logger.warning("No events found during monitoring")
            current_state['current_stage'] = WorkflowStage.COMPLETE.value
        
    except Exception as e:
        error_msg = f"Monitoring error: {str(e)}"
        logger.error(error_msg)
        current_state['errors'] = current_state.get('errors', []) + [error_msg]
        current_state['current_stage'] = WorkflowStage.ERROR.value
    
    return current_state

async def analyze_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze events and identify patterns."""
    current_state = state.copy() if state else create_empty_state()
    logger.info("Starting analysis phase")
    
    try:
        logger.info(f"Analyzing {len(current_state.get('events', []))} events")
        # TODO: Implement pattern analysis
        current_state['current_stage'] = WorkflowStage.REPORTING.value
        
    except Exception as e:
        error_msg = f"Analysis error: {str(e)}"
        logger.error(error_msg)
        current_state['errors'] = current_state.get('errors', []) + [error_msg]
        current_state['current_stage'] = WorkflowStage.ERROR.value
    
    return current_state

async def report_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Generate Gonzo's insights and commentary."""
    current_state = state.copy() if state else create_empty_state()
    logger.info("Starting reporting phase")
    
    try:
        logger.info(f"Generating insights from {len(current_state.get('patterns', []))} patterns")
        # TODO: Implement insight generation
        current_state['current_stage'] = WorkflowStage.COMPLETE.value
        
    except Exception as e:
        error_msg = f"Reporting error: {str(e)}"
        logger.error(error_msg)
        current_state['errors'] = current_state.get('errors', []) + [error_msg]
        current_state['current_stage'] = WorkflowStage.ERROR.value
    
    return current_state

async def error_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Handle errors and recovery."""
    current_state = state.copy() if state else create_empty_state()
    
    # Log errors
    if current_state.get('errors'):
        for error in current_state['errors']:
            logger.error(f"Error encountered: {error}")
        current_state['errors'] = []
    
    current_state['current_stage'] = WorkflowStage.COMPLETE.value
    return current_state

def get_stage(state: Dict[str, Any]) -> str:
    """Get stage value from state."""
    if not state or 'current_stage' not in state:
        return WorkflowStage.MONITORING.value
    return state['current_stage']

def create_workflow(config: Optional[Dict[str, Any]] = None) -> Tuple[StateGraph, MemorySaver]:
    """Create the simplified workflow graph and memory saver."""
    # Create workflow with state schema
    workflow = StateGraph(state_schema=GonzoGraphState)
    
    # Add nodes
    workflow.add_node("monitor", monitor_node)
    workflow.add_node("analyze", analyze_node)
    workflow.add_node("report", report_node)
    workflow.add_node("error", error_node)
    
    # Add edges based on current_stage
    workflow.add_conditional_edges(
        "monitor",
        get_stage,
        {
            WorkflowStage.ANALYSIS.value: "analyze",
            WorkflowStage.ERROR.value: "error",
            WorkflowStage.COMPLETE.value: END
        }
    )
    
    workflow.add_conditional_edges(
        "analyze",
        get_stage,
        {
            WorkflowStage.REPORTING.value: "report",
            WorkflowStage.ERROR.value: "error",
            WorkflowStage.COMPLETE.value: END
        }
    )
    
    workflow.add_conditional_edges(
        "report",
        get_stage,
        {
            WorkflowStage.COMPLETE.value: END,
            WorkflowStage.ERROR.value: "error"
        }
    )
    
    workflow.add_conditional_edges(
        "error",
        get_stage,
        {
            WorkflowStage.COMPLETE.value: END
        }
    )
    
    # Set entry point
    workflow.set_entry_point("monitor")
    
    # Create memory saver
    memory = MemorySaver()
    
    return workflow, memory