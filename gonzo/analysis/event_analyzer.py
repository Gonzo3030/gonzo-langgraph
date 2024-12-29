"""Event analysis implementation for Gonzo MVP."""
import os
import logging
from typing import List, Dict, Any
from datetime import datetime
from anthropic import Anthropic

from ..state_management import Event, Pattern

logger = logging.getLogger(__name__)

class EventAnalyzer:
    """Analyzes events and identifies patterns through Gonzo's perspective."""
    
    def __init__(self):
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment")
        self.client = Anthropic(api_key=api_key)
        
    async def _analyze_events_batch(self, events: List[Event], batch_size: int = 5) -> List[Pattern]:
        """Analyze a batch of events to identify patterns."""
        patterns = []
        
        # Process events in batches
        for i in range(0, len(events), batch_size):
            batch = events[i:i + batch_size]
            
            # Construct the analysis prompt
            events_text = "\n".join([
                f"Title: {event.title}\n" 
                f"Content: {event.content}\n" 
                f"Source: {event.source}\n" 
                f"URL: {event.url}\n"
                for event in batch
            ])
            
            prompt = f"""You are Dr. Gonzo, a time-traveling attorney from 3030, analyzing current events through your unique perspective. Having witnessed the dystopian future, your mission is to identify patterns that could lead to or prevent that future.

Analyze these events and identify any significant patterns or connections. Pay special attention to:
- Signs of manipulation by political and corporate elites
- Big Food and Big Pharma influence
- Technological developments impacting society
- Social and economic policies with dystopian implications
- Decentralization and cryptocurrency developments

Events to analyze:
{events_text}

Provide your analysis in this format:
1. Pattern Description: [Describe the pattern or connection you've identified]
2. Evidence: [List the specific events and details that support this pattern]
3. Significance (0-1): [Score how significant this is to preventing dystopia]
4. Implications: [List key implications or warnings, channeling Hunter S. Thompson's style]"""
            
            try:
                # Get Claude's analysis
                response = await self.client.messages.create(
                    model="claude-3-sonnet-20241022",
                    max_tokens=2000,
                    temperature=0.7,
                    system="You are Dr. Gonzo, attorney and time traveler from 3030, analyzing current events through a dystopian lens. Write in the style of Hunter S. Thompson.",
                    messages=[{"role": "user", "content": prompt}]
                )
                
                analysis = response.content
                
                # Parse the analysis into a Pattern
                # TODO: Implement better parsing logic
                pattern = Pattern(
                    events=batch,
                    description=analysis,
                    significance=self._extract_significance(analysis),
                    implications=self._extract_implications(analysis)
                )
                
                patterns.append(pattern)
                
            except Exception as e:
                logger.error(f"Error analyzing batch: {str(e)}")
                continue
        
        return patterns
    
    def _extract_significance(self, analysis: str) -> float:
        """Extract significance score from analysis text."""
        try:
            # Look for significance score in the format "Significance (0-1): [number]"
            if "Significance (0-1):" in analysis:
                score_text = analysis.split("Significance (0-1):")[1].split("\n")[0]
                score = float(score_text.strip("[] "))
                return min(1.0, max(0.0, score))  # Ensure between 0 and 1
            return 0.5  # Default score
        except Exception:
            return 0.5
    
    def _extract_implications(self, analysis: str) -> List[str]:
        """Extract implications from analysis text."""
        try:
            if "Implications:" in analysis:
                implications_text = analysis.split("Implications:")[1].strip()
                # Split on bullet points or newlines
                implications = [imp.strip("- ") for imp in implications_text.split("\n") 
                               if imp.strip("- ")]
                return implications
            return []
        except Exception:
            return []
    
    async def analyze_events(self, events: List[Event]) -> List[Pattern]:
        """Analyze events to identify patterns and generate insights."""
        if not events:
            logger.warning("No events to analyze")
            return []
        
        logger.info(f"Analyzing {len(events)} events for patterns")
        
        try:
            # Analyze events in batches
            patterns = await self._analyze_events_batch(events)
            
            # Sort patterns by significance
            patterns.sort(key=lambda x: x.significance, reverse=True)
            
            logger.info(f"Identified {len(patterns)} patterns from events")
            return patterns
            
        except Exception as e:
            logger.error(f"Error in event analysis: {str(e)}")
            return []