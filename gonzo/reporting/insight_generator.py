"""Insight generation for Twitter reporting with enhanced Gonzo voice."""
import os
import logging
from typing import List, Dict, Any
from datetime import datetime
from anthropic import Anthropic

from ..state_management import Pattern

logger = logging.getLogger(__name__)

class InsightGenerator:
    """Generates Twitter-ready insights in Gonzo's voice."""
    
    def __init__(self):
        self.client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        
    def _create_thread_prompt(self, pattern: Pattern) -> str:
        """Create prompt for generating a Twitter thread."""
        return f"""You are Dr. Gonzo, the infamous attorney who vanished in Mexico in 1974, now existing in the dystopian world of 3030. You're communicating across time via Twitter threads, warning people about the patterns you see leading to the dark future you inhabit.

Your voice combines:
- Hunter S. Thompson-style gonzo journalism
- Legal expertise from your attorney days
- Dark knowledge of humanity's descent (1974-3030)
- Paranoid but insightful observations from 3030

Create a Twitter thread (max 5 tweets) about this pattern you've identified. Each tweet must be under 280 characters.

Pattern to report on:
{pattern.description}

Significance: {pattern.significance}
Implications: {', '.join(pattern.implications)}

Your thread should:
- Start with a timestamped transmission from 3030
- Connect current events to future outcomes
- Include personal experiences when relevant
- Maintain your paranoid but insightful tone
- End with a warning or call to action

Format as:
[Tweet 1]
[Tweet 2]
etc.

Remember: You're trying to prevent the dystopian future you're living in, but don't reveal everything at once. Maintain some mystery about your existence and the resistance."""

    async def generate_thread(self, pattern: Pattern) -> List[str]:
        """Generate a Twitter thread for a pattern."""
        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1000,
                temperature=0.7,
                system="You are Dr. Gonzo from 3030, writing Twitter threads in Hunter S. Thompson's style while warning about dystopian futures.",
                messages=[{"role": "user", "content": self._create_thread_prompt(pattern)}]
            )
            
            # Extract tweets from response
            content = response.content[0].text if hasattr(response.content[0], 'text') else str(response.content)
            tweets = [tweet.strip() for tweet in content.split('[Tweet') if tweet.strip()]
            tweets = [tweet.split(']')[1].strip() if ']' in tweet else tweet.strip() for tweet in tweets]
            
            logger.info(f"Generated thread with {len(tweets)} tweets")
            return tweets
            
        except Exception as e:
            logger.error(f"Error generating thread: {str(e)}")
            return []
            
    async def generate_insights(self, patterns: List[Pattern]) -> List[Dict[str, Any]]:
        """Generate Twitter threads for each significant pattern."""
        insights = []
        
        for pattern in patterns:
            # Debug log the pattern and its significance
            logger.info(f"Processing pattern with significance {pattern.significance}")
            logger.debug(f"Pattern details: {pattern.model_dump()}")
            
            # Generate thread for pattern
            tweets = await self.generate_thread(pattern)
            if tweets:
                insight = {
                    'pattern': pattern.model_dump(),
                    'thread': tweets,
                    'timestamp': datetime.now().isoformat()
                }
                insights.append(insight)
                logger.info(f"Generated insight with {len(tweets)} tweets")
        
        logger.info(f"Generated {len(insights)} total insights")
        return insights