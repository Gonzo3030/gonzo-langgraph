"""Insight generation for Twitter reporting."""
import os
import logging
from typing import List, Dict, Any
from datetime import datetime
from anthropic import Anthropic

from ..state_management import Pattern, Insight

logger = logging.getLogger(__name__)

class InsightGenerator:
    """Generates Twitter-ready insights from patterns."""
    
    def __init__(self):
        self.client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        
    def _create_thread_prompt(self, pattern: Pattern) -> str:
        """Create prompt for generating a Twitter thread."""
        return f"""You are Dr. Gonzo, attorney and time traveler from 3030, reporting on disturbing patterns you've discovered. Create a Twitter thread (max 5 tweets) about this pattern. Each tweet should be max 280 characters.

Pattern to report on:
Description: {pattern.description}
Evidence: {', '.join(pattern.evidence) if hasattr(pattern, 'evidence') else 'N/A'}
Significance: {pattern.significance}
Implications: {', '.join(pattern.implications)}

Write in Hunter S. Thompson's gonzo style - paranoid, insightful, and with dark humor. Include relevant hashtags. Format as:
[Tweet 1]
[Tweet 2]
etc.

Remember: You're warning people about the dystopian future you've witnessed."""

    async def generate_thread(self, pattern: Pattern) -> List[str]:
        """Generate a Twitter thread for a pattern."""
        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1000,
                temperature=0.7,
                system="You are Dr. Gonzo from 3030, writing Twitter threads in Hunter S. Thompson's style.",
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
            # Only create threads for significant patterns
            if pattern.significance >= 0.7:
                logger.info(f"Generating thread for pattern with significance {pattern.significance}")
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