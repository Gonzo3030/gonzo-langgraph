"""X posting node for Gonzo."""

from typing import Dict, Any
from datetime import datetime
from ..integrations.x_client import XClient
from ..types import GonzoState

async def post_to_x(state: GonzoState) -> Dict[str, Any]:
    """Post content to X."""
    try:
        # Skip if no content to post
        if not state.response.queued_responses:
            return {
                "timestamp": state.timestamp,
                "next": "detect"
            }
            
        # Initialize X client
        x_client = XClient(
            api_key=state.memory.short_term.get('x_api_key'),
            api_agent=None  # Using direct API mode for now
        )
        
        # Post thread
        thread_id = None
        posted_ids = []
        
        for tweet in state.response.queued_responses:
            # Post as reply if we have a thread going
            if thread_id:
                result = await x_client.post_tweet(tweet, use_agent=False)
                posted_ids.append(result['id'])
                thread_id = result['id']
            else:
                # Start new thread
                result = await x_client.post_tweet(tweet, use_agent=False)
                posted_ids.append(result['id'])
                thread_id = result['id']
        
        # Update state
        state.x_state = {
            'last_thread_id': thread_id,
            'posted_ids': posted_ids,
            'timestamp': datetime.now().isoformat()
        }
        state.timestamp = datetime.now()
        
        # Clear posted responses
        state.response.queued_responses = []
        
        return {
            "x_state": state.x_state,
            "response": state.response,
            "timestamp": state.timestamp,
            "next": "detect"
        }
        
    except Exception as e:
        state.add_error(f"X posting error: {str(e)}")
        return {
            "memory": state.memory,
            "timestamp": state.timestamp,
            "next": "error"
        }