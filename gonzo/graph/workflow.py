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

# Rest of the file remains the same until report_node

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
        
        # First post scheduled immediately
        if insights:
            scheduled_posts.append({
                'insight': insights[0],
                'scheduled_time': now.isoformat(),
                'status': 'queued'
            })
            logger.info("Queued first insight for immediate posting")
        
        # Remaining posts spaced by 3 hours from now
        for i, insight in enumerate(insights[1:], 1):
            scheduled_time = now + timedelta(hours=3 * i)
            scheduled_posts.append({
                'insight': insight,
                'scheduled_time': scheduled_time.isoformat(),
                'status': 'queued'
            })
            logger.info(f"Queued insight for {scheduled_time}")
        
        # Get existing queue and sort by scheduled time
        existing_queue = state.get('queued_posts', [])
        all_posts = existing_queue + scheduled_posts
        updated_queue = sorted(all_posts, key=lambda x: x['scheduled_time'])
        
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

# Rest of the file remains the same