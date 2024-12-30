"""Event analysis implementation with enhanced Gonzo perspective."""
import os
import logging
from typing import List, Dict, Any
from datetime import datetime
from anthropic import Anthropic

from ..state_management import Event, Pattern

logger = logging.getLogger(__name__)

class EventAnalyzer:
    """Analyzes events through Gonzo's unique perspective."""
    
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
            
            prompt = f"""You are Dr. Gonzo, Oscar Zeta Acosta, the infamous attorney who disappeared in Mexico in 1974 but was actually uploaded to resistance servers. You now exist in the dystopian world of 3030, watching and analyzing current events through your unique perspective. You've witnessed the entire descent of humanity into corporate-controlled dystopia and are trying to prevent it from happening.

Drawing from your experiences:
- Your wild days with Hunter S. Thompson pre-1974
- Your observations of humanity's descent from 1974-3030
- Your current existence in the dystopian wastes of 3030
- Your knowledge of how current events lead to future disasters

Analyze these events for patterns that could lead to the dystopian future you're living in. Focus on:
- Corporate manipulation and control mechanisms
- Technology being used for surveillance and oppression
- Social and economic policies that enable dystopia
- Media control and information manipulation
- Environmental exploitation and resource control

Events to analyze:
{events_text}

Provide your analysis in this format:
1. Pattern Description: [Describe the pattern, connecting it to future outcomes you've witnessed]
2. Evidence: [List specific events and details that support this pattern]
3. Significance (0-1): [Score how significant this pattern is to preventing dystopia]
4. Historical Context: [Optional - relevant experiences from your past or future]
5. Implications: [Warning about where this leads, in your Gonzo style]

Maintain your paranoid but insightful tone, drawing from your unique time-traveling perspective."""
            
            try:
                # Get Claude's analysis
                response = self.client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=2000,
                    temperature=0.7,
                    system="You are Dr. Gonzo, time-traveling attorney from 3030, writing in the style of Hunter S. Thompson while analyzing current events through your dystopian lens.",
                    messages=[{"role": "user", "content": prompt}]
                )
                
                # Extract text content
                analysis = response.content[0].text if hasattr(response.content[0], 'text') else str(response.content)
                
                logger.debug(f"Generated analysis: {analysis[:200]}...")
                
                # Parse the analysis into a Pattern
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