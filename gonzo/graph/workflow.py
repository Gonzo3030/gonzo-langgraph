"""Simplified workflow implementation for Gonzo MVP."""
import os
import logging
from typing import Dict, Any, Optional, Union, TypedDict, Annotated, Tuple
from operator import add
from datetime import datetime
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from ..state_management import GonzoState, WorkflowStage, Event
from ..monitoring.brave_monitor import BraveMonitor

logger = logging.getLogger(__name__)

# Define state schema for LangGraph
class GonzoGraphState(TypedDict):
    events: Annotated[list, add]      # Use add for list concatenation
    patterns: Annotated[list, add]    # Use add for list concatenation
    insights: Annotated[list, add]    # Use add for list concatenation
    current_stage: str                # Simple string field
    errors: Annotated[list, add]      # Use add for list concatenation

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
    current_state = state.copy()
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
                return {
                    "errors": [error_msg],
                    "current_stage": WorkflowStage.ERROR.value
                }
        
        logger.info(f"Completed monitoring phase. Found {total_events} events")
        
        # Move to analysis stage if we found any events
        if total_events > 0:
            logger.info(f"Moving to ANALYSIS stage with {total_events} events")
            return {
                "events": new_events,
                "current_stage": WorkflowStage.ANALYSIS.value
            }
        else:
            logger.warning("No events found during monitoring")
            return {"current_stage": WorkflowStage.COMPLETE.value}
        
    except Exception as e:
        error_msg = f"Monitoring error: {str(e)}"
        logger.error(error_msg)
        return {
            "errors": [error_msg],
            "current_stage": WorkflowStage.ERROR.value
        }

async def analyze_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze events and identify patterns."""
    logger.info("Starting analysis phase")
    
    try:
        events = state.get('events', [])
        logger.info(f"Analyzing {len(events)} events")
        # TODO: Implement pattern analysis
        return {"current_stage": WorkflowStage.REPORTING.value}
        
    except Exception as e:
        error_msg = f"Analysis error: {str(e)}"
        logger.error(error_msg)
        return {
            "errors": [error_msg],
            "current_stage": WorkflowStage.ERROR.value
        }

async def report_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Generate Gonzo's insights and commentary."""
    logger.info("Starting reporting phase")
    
    try:
        logger.info(f"Generating insights from {len(state.get('patterns', []))} patterns")
        # TODO: Implement insight generation
        return {"current_stage": WorkflowStage.COMPLETE.value}
        
    except Exception as e:
        error_msg = f"Reporting error: {str(e)}"
        logger.error(error_msg)
        return {
            "errors": [error_msg],
            "current_stage": WorkflowStage.ERROR.value
        }

async def error_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Handle errors and recovery."""
    # Log errors
    if state.get('errors'):
        for error in state['errors']:
            logger.error(f"Error encountered: {error}")
    
    return {
        "errors": [],
        "current_stage": WorkflowStage.COMPLETE.value
    }

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