"""Simplified workflow implementation for Gonzo MVP."""
import os
import logging
from typing import Dict, Any, Optional, Union
from datetime import datetime
from langgraph.graph import StateGraph, END
from langgraph.pregel import BaseNode

from ..state_management import GonzoState, WorkflowStage, Event
from ..monitoring.brave_monitor import BraveMonitor

logger = logging.getLogger(__name__)

class MonitorNode(BaseNode):
    """Node for monitoring news and events."""
    async def invoke(self, state: Dict) -> Dict[str, Any]:
        state_obj = GonzoState(**state)
        logger.info("Starting monitoring phase")
        
        try:
            api_key = os.getenv('BRAVE_API_KEY')
            if not api_key:
                raise ValueError("BRAVE_API_KEY not found in environment")
                
            monitor = BraveMonitor(api_key)
            logger.info("Initialized Brave monitor")
            
            queries = monitor.generate_queries()
            
            # Initialize a fresh events list
            state_obj.events = []
            total_events = 0
            
            for query in queries:
                try:
                    logger.info(f"Processing query: {query}")
                    news_items = await monitor.search_news(query)
                    
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
            state_obj.current_stage = (
                WorkflowStage.ANALYSIS if total_events > 0
                else WorkflowStage.COMPLETE
            )
            
            if total_events > 0:
                logger.info(f"Moving to ANALYSIS stage with {len(state_obj.events)} events")
            else:
                logger.warning("No events found during monitoring")
            
        except Exception as e:
            error_msg = f"Monitoring error: {str(e)}"
            logger.error(error_msg)
            state_obj.errors.append(error_msg)
            state_obj.current_stage = WorkflowStage.ERROR
        
        return state_obj.model_dump()

class AnalyzeNode(BaseNode):
    """Node for analyzing events and identifying patterns."""
    async def invoke(self, state: Dict) -> Dict[str, Any]:
        state_obj = GonzoState(**state)
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
        
        return state_obj.model_dump()

class ReportNode(BaseNode):
    """Node for generating insights and commentary."""
    async def invoke(self, state: Dict) -> Dict[str, Any]:
        state_obj = GonzoState(**state)
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
        
        return state_obj.model_dump()

class ErrorNode(BaseNode):
    """Node for handling errors and recovery."""
    async def invoke(self, state: Dict) -> Dict[str, Any]:
        state_obj = GonzoState(**state)
        
        if state_obj.errors:
            for error in state_obj.errors:
                logger.error(f"Error encountered: {error}")
            state_obj.errors.clear()
        
        state_obj.current_stage = WorkflowStage.COMPLETE
        return state_obj.model_dump()

def create_workflow(config: Optional[Dict[str, Any]] = None) -> StateGraph:
    """Create the simplified workflow graph."""
    workflow = StateGraph()
    
    # Add nodes
    workflow.add_node("monitor", MonitorNode())
    workflow.add_node("analyze", AnalyzeNode())
    workflow.add_node("report", ReportNode())
    workflow.add_node("error", ErrorNode())
    
    # Add edges based on current_stage
    def get_stage(state: Dict) -> str:
        return GonzoState(**state).current_stage.value
    
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