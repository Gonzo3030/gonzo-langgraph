"""Simplified workflow implementation for Gonzo MVP."""
import os
import logging
from typing import Dict, Any, Optional, Union, Tuple
from operator import add
from datetime import datetime
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from ..state_management import GonzoState, WorkflowStage, Event, Pattern, GonzoGraphState
from ..monitoring.brave_monitor import BraveMonitor
from ..analysis.event_analyzer import EventAnalyzer
from ..reporting.insight_generator import InsightGenerator
from ..publishing.publisher import Publisher

logger = logging.getLogger(__name__)

# ... [Previous monitor_node and analyze_node implementations remain the same] ...

async def report_node(state: GonzoGraphState) -> Dict[str, Any]:
    """Generate Gonzo's insights and commentary."""
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
        
        # Publish insights
        try:
            publisher = Publisher.from_env(wait_time=1.0)
            publish_results = await publisher.publish_insights(insights)
            logger.info(f"Published {len(publish_results)} threads to X")
            
            return {
                "insights": insights,
                "published": publish_results,
                "current_stage": WorkflowStage.COMPLETE.value
            }
            
        except Exception as e:
            logger.error(f"Error publishing to X: {str(e)}")
            return {
                "insights": insights,
                "current_stage": WorkflowStage.COMPLETE.value
            }
        
    except Exception as e:
        error_msg = f"Reporting error: {str(e)}"
        logger.error(error_msg)
        return {
            "errors": [error_msg],
            "current_stage": WorkflowStage.ERROR.value
        }

# ... [Rest of the workflow.py implementation remains the same] ...