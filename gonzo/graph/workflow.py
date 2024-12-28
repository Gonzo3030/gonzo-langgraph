"""Simplified workflow implementation for Gonzo MVP."""
import os
import logging
from typing import Dict, Any, Optional, Union
from datetime import datetime
from langgraph.graph import StateGraph, END

from ..state_management import GonzoState, WorkflowStage, Event
from ..monitoring.brave_monitor import BraveMonitor

logger = logging.getLogger(__name__)

def ensure_state_dict(state: Union[Dict, GonzoState]) -> Dict:
    """Ensure we're working with a dictionary"""
    if isinstance(state, GonzoState):
        state_dict = state.model_dump()
        # Convert enum to string
        if isinstance(state_dict.get('current_stage'), WorkflowStage):
            state_dict['current_stage'] = state_dict['current_stage'].value
        return state_dict
    if isinstance(state, dict) and isinstance(state.get('current_stage'), WorkflowStage):
        state['current_stage'] = state['current_stage'].value
    return state

def ensure_state_obj(state: Union[Dict, GonzoState]) -> GonzoState:
    """Ensure we're working with a GonzoState object"""
    if isinstance(state, GonzoState):
        return state
        
    state_dict = state.copy()  # Make a copy to avoid modifying the input
    if isinstance(state_dict.get('current_stage'), str):
        state_dict['current_stage'] = WorkflowStage(state_dict['current_stage'])
    return GonzoState(**state_dict)

async def monitor_node(state: Union[Dict, GonzoState]) -> Dict[str, Any]:
    """Monitor for relevant events using Brave API."""
    state_dict = ensure_state_dict(state)
    state_obj = ensure_state_obj(state_dict)
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
        
        # Initialize a fresh events list
        state_obj.events = []
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
                    state_obj.events.append(event)
                    total_events += 1
                    
            except Exception as e:
                error_msg = f"Error searching {query}: {str(e)}"
                logger.error(error_msg)
                state_obj.errors.append(error_msg)
        
        logger.info(f"Completed monitoring phase. Found {total_events} events")
        
        # Move to analysis stage if we found any events
        if total_events > 0:
            state_obj.current_stage = WorkflowStage.ANALYSIS
            logger.info(f"Moving to ANALYSIS stage with {len(state_obj.events)} events")
        else:
            logger.warning("No events found during monitoring")
            state_obj.current_stage = WorkflowStage.COMPLETE
        
    except Exception as e:
        error_msg = f"Monitoring error: {str(e)}"
        logger.error(error_msg)
        state_obj.errors.append(error_msg)
        state_obj.current_stage = WorkflowStage.ERROR
    
    return ensure_state_dict(state_obj)

async def analyze_node(state: Union[Dict, GonzoState]) -> Dict[str, Any]:
    """Analyze events and identify patterns."""
    state_dict = ensure_state_dict(state)
    state_obj = ensure_state_obj(state_dict)
    logger.info("Starting analysis phase")
    
    try:
        logger.info(f"Analyzing {len(state_obj.events)} events")
        # TODO: Implement pattern analysis
        state_obj.current_stage = WorkflowStage.REPORTING
        
    except Exception as e:
        error_msg = f"Analysis error: {str(e)}"
        logger.error(error_msg)
        state_obj.errors.append(error_msg)
        state_obj.current_stage = WorkflowStage.ERROR
    
    return ensure_state_dict(state_obj)

async def report_node(state: Union[Dict, GonzoState]) -> Dict[str, Any]:
    """Generate Gonzo's insights and commentary."""
    state_dict = ensure_state_dict(state)
    state_obj = ensure_state_obj(state_dict)
    logger.info("Starting reporting phase")
    
    try:
        logger.info(f"Generating insights from {len(state_obj.patterns)} patterns")
        # TODO: Implement insight generation
        state_obj.current_stage = WorkflowStage.COMPLETE
        
    except Exception as e:
        error_msg = f"Reporting error: {str(e)}"
        logger.error(error_msg)
        state_obj.errors.append(error_msg)
        state_obj.current_stage = WorkflowStage.ERROR
    
    return ensure_state_dict(state_obj)

async def error_node(state: Union[Dict, GonzoState]) -> Dict[str, Any]:
    """Handle errors and recovery."""
    state_dict = ensure_state_dict(state)
    state_obj = ensure_state_obj(state_dict)
    
    # Log errors
    if state_obj.errors:
        for error in state_obj.errors:
            logger.error(f"Error encountered: {error}")
        state_obj.errors.clear()
    
    state_obj.current_stage = WorkflowStage.COMPLETE
    return ensure_state_dict(state_obj)

def get_stage(state: Union[Dict, GonzoState]) -> str:
    """Get stage value, handling both dict and GonzoState inputs"""
    state_dict = ensure_state_dict(state)
    return state_dict['current_stage']

def create_workflow(config: Optional[Dict[str, Any]] = None) -> StateGraph:
    """Create the simplified workflow graph."""
    # Create workflow
    workflow = StateGraph()
    
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
    
    return workflow