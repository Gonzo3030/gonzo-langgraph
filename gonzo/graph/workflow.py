"""Main content generation workflow for Gonzo."""
import os
import logging
from typing import Dict, Any, Optional, Union, Tuple
from operator import add
from datetime import datetime, timedelta
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from ..state_management import GonzoState, WorkflowStage, Event, Pattern, GonzoGraphState
from ..monitoring.brave_monitor import BraveMonitor
from ..analysis.event_analyzer import EventAnalyzer
from ..reporting.insight_generator import InsightGenerator

logger = logging.getLogger(__name__)

async def monitor_node(state: GonzoGraphState) -> Dict[str, Any]:
    """Monitor for relevant events using Brave API."""
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
                    
            except Exception as e:
                error_msg = f"Error searching {query}: {str(e)}"
                logger.error(error_msg)
                return {
                    "errors": [error_msg],
                    "current_stage": WorkflowStage.ERROR.value
                }
        
        total_events = len(new_events)
        logger.info(f"Completed monitoring phase. Found {total_events} events")
        
        # Return only the changed fields
        if total_events > 0:
            logger.info(f"Moving to ANALYSIS stage with {total_events} events")
            return {
                "events": new_events,
                "current_stage": WorkflowStage.ANALYSIS.value
            }
        else:
            logger.warning("No events found during monitoring")
            return {
                "current_stage": WorkflowStage.COMPLETE.value
            }
        
    except Exception as e:
        error_msg = f"Monitoring error: {str(e)}"
        logger.error(error_msg)
        return {
            "errors": [error_msg],
            "current_stage": WorkflowStage.ERROR.value
        }

async def analyze_node(state: GonzoGraphState) -> Dict[str, Any]:
    """Analyze events and identify patterns."""
    logger.info("Starting analysis phase")
    
    try:
        # Get events from state
        events = [Event(**event_data) for event_data in state.get('events', [])]
        logger.info(f"Analyzing {len(events)} events")
        
        if not events:
            logger.warning("No events to analyze")
            return {
                "current_stage": WorkflowStage.COMPLETE.value
            }
        
        # Initialize analyzer
        analyzer = EventAnalyzer()
        
        # Analyze events
        patterns = await analyzer.analyze_events(events)
        
        # Convert patterns to dict for state
        pattern_dicts = [pattern.model_dump() for pattern in patterns]
        
        logger.info(f"Analysis complete. Found {len(patterns)} patterns")
        
        return {
            "patterns": pattern_dicts,
            "current_stage": WorkflowStage.REPORTING.value
        }
        
    except Exception as e:
        error_msg = f"Analysis error: {str(e)}"
        logger.error(error_msg)
        return {
            "errors": [error_msg],
            "current_stage": WorkflowStage.ERROR.value
        }

async def report_node(state: GonzoGraphState) -> Dict[str, Any]:
    """Generate Gonzo's insights and queue them for publishing."""
    logger.info("Starting reporting phase")
    
    try:
        patterns = [Pattern(**p) for p in state.get('patterns', [])]
        logger.info(f"Generating insights from {len(patterns)} patterns")
        
        if not patterns:
            logger.warning("No patterns to generate insights from")
            return {
                "current_stage": WorkflowStage.COMPLETE.value
            }
        
        # Generate insights
        generator = InsightGenerator()
        insights = await generator.generate_insights(patterns)
        
        logger.info(f"Generated {len(insights)} Twitter threads")
        
        # Schedule insights
        now = datetime.now()
        scheduled_posts = []
        
        for i, insight in enumerate(insights):
            # Schedule posts with 30-minute gaps
            scheduled_time = now + timedelta(minutes=30 * i)
            scheduled_posts.append({
                'insight': insight,
                'scheduled_time': scheduled_time.isoformat(),
                'status': 'queued'
            })
            logger.info(f"Queued insight for {scheduled_time}")
        
        # Get existing queue
        existing_queue = state.get('queued_posts', [])
        updated_queue = existing_queue + scheduled_posts
        
        logger.info(f"Added {len(scheduled_posts)} posts to queue. Total queued: {len(updated_queue)}")
        
        return {
            "insights": insights,
            "queued_posts": updated_queue,
            "current_stage": WorkflowStage.COMPLETE.value
        }
        
    except Exception as e:
        error_msg = f"Reporting error: {str(e)}"
        logger.error(error_msg)
        return {
            "errors": [error_msg],
            "current_stage": WorkflowStage.ERROR.value
        }

async def error_node(state: GonzoGraphState) -> Dict[str, Any]:
    """Handle errors and recovery."""
    # Log errors
    if state.get('errors'):
        for error in state['errors']:
            logger.error(f"Error encountered: {error}")
    
    return {
        "errors": [],
        "current_stage": WorkflowStage.COMPLETE.value
    }

def get_stage(state: GonzoGraphState) -> str:
    """Get stage value from state."""
    return state.get('current_stage', WorkflowStage.MONITORING.value)

def create_workflow(config: Optional[Dict[str, Any]] = None) -> Tuple[StateGraph, MemorySaver]:
    """Create the content generation workflow graph."""
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
    workflow.add_edge(START, "monitor")
    
    # Create memory saver
    memory = MemorySaver()
    
    return workflow, memory