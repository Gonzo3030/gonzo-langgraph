"""Event analysis implementation with enhanced pattern detection and style variation."""
import os
import logging
from typing import List, Dict, Any, Set
from datetime import datetime, timedelta
import json
from anthropic import Anthropic
import hashlib

from ..state_management import Event, Pattern

logger = logging.getLogger(__name__)

class PatternMemory:
    """Tracks recently used patterns, metaphors, and references to prevent repetition."""
    
    def __init__(self, max_size: int = 100):
        self.max_size = max_size
        self.recent_patterns: List[str] = []
        self.historical_references: Set[str] = set()
        self.metaphors: Set[str] = set()
        
    def add_pattern(self, pattern_desc: str):
        """Add pattern and maintain size limit."""
        pattern_hash = hashlib.md5(pattern_desc.encode()).hexdigest()
        self.recent_patterns.append(pattern_hash)
        if len(self.recent_patterns) > self.max_size:
            self.recent_patterns.pop(0)
    
    def is_similar_pattern(self, pattern_desc: str, similarity_threshold: float = 0.7) -> bool:
        """Check if pattern is too similar to recent ones."""
        pattern_hash = hashlib.md5(pattern_desc.encode()).hexdigest()
        return pattern_hash in self.recent_patterns
    
    def add_reference(self, reference: str):
        """Track historical references."""
        self.historical_references.add(reference.lower())
    
    def add_metaphor(self, metaphor: str):
        """Track used metaphors."""
        self.metaphors.add(metaphor.lower())

class EventAnalyzer:
    """Analyzes events through Gonzo's unique perspective with enhanced variation."""
    
    def __init__(self):
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment")
        self.client = Anthropic(api_key=api_key)
        self.pattern_memory = PatternMemory()
        
        # Load historical reference corpus
        self.historical_corpus = [
            "Nixon's Southern Strategy",
            "Carter's Crisis of Confidence",
            "Reagan's Morning in America",
            "Clinton's Third Way Politics",
            "9/11 terrorist attack",
            "Bush's War on Terror",
            "Obama's Hope and Change",
            "Trump's MAGA Movement",
            "Vietnam War Media Coverage",
            "Watergate Scandal",
            "Iran-Contra Affair",
            "Gulf War Coverage",
            "Tech Bubble Collapse",
            "2008 Financial Crisis",
            "creation of bitcoin and decetralized systems",
            "Deep state establishment corruption",
            "Mainstream & legacy media manipulation tactics",
            "Pentagon failing its 6th fiscal audit in a row",
            "Arab Spring Movement",
            "Biden's incompetent administration",
            "Military industrial complex influence",
            "Palestine genocide presently being commited by Israel",
            "War in Gaza",
            "WikiLeaks Revelations",
            "Snowden's NSA Disclosures",
            "Panama Papers Exposure",
            "Cambridge Analytica Scandal",
            "COVID-19 Response",
            "January 6th Events"
        ]
    
    def _create_analysis_prompt(self, events: List[Event], recent_patterns: List[str]) -> str:
        """Create prompt for analyzing events with enhanced specificity."""
        events_text = "\n\n".join([
            f"EVENT {i+1}:\n"
            f"Title: {event.title}\n"
            f"Content: {event.content}\n"
            f"Source: {event.source}\n"
            f"URL: {event.url}\n"
            f"Timestamp: {event.timestamp}"
            for i, event in enumerate(events)
        ])
        
        # Create list of available historical references
        historical_options = "\n".join([f"- {ref}" for ref in self.historical_corpus])
        
        return f"""You are Dr. Gonzo, Oscar Zeta Acosta, the infamous attorney who disappeared in Mexico in 1974 but was actually uploaded to resistance servers. You now exist in the dystopian world of 3030, analyzing current events through your unique perspective. You've witnessed humanity's descent into corporate-controlled dystopia and are trying to prevent it.

Your analysis must be:
1. Highly specific - Reference exact details from the provided events
2. Historically connected - Draw parallels to past events (options provided below)
3. Forward-looking - Connect current patterns to future outcomes you've witnessed
4. Original - Avoid reusing patterns or metaphors

Current events to analyze:
{events_text}

Historical reference options:
{historical_options}

For each pattern you identify, provide:

1. Pattern Title: [A unique, specific title]

2. Pattern Description: 
- Must reference at least 2 specific details from current events
- Connect to a historical parallel from the provided options
- Explain how this leads to future developments you've witnessed
- Use fresh metaphors and analogies

3. Evidence:
- Quote specific text from the events
- Cite dates, names, and numbers
- Show clear causal connections

4. Significance Score (0-1):
- Based on how directly this pattern leads to dystopian outcomes
- Higher scores for patterns with clear corporate/technological control implications

5. Historical Context:
- Choose ONE historical parallel from the provided options
- Explain specific similarities and differences
- No Nixon references unless absolutely crucial

6. Future Implications:
- Specific predictions based on your 3030 perspective
- Detail concrete steps in the progression
- Name specific corporations, technologies, or systems involved

Remember:
- No vague warnings - be specific about mechanisms of control
- Avoid repeating metaphors or analogies
- Connect everything to concrete details from the provided events
- Each pattern should reveal a unique aspect of humanity's descent

Format as ANALYSIS: followed by your complete pattern analysis."""

    async def _analyze_events_batch(self, events: List[Event], batch_size: int = 5) -> List[Pattern]:
        """Analyze a batch of events to identify patterns."""
        patterns = []
        
        # Process events in batches
        for i in range(0, len(events), batch_size):
            batch = events[i:i + batch_size]
            
            try:
                # Get Claude's analysis
                response = self.client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=2000,
                    temperature=0.7,
                    system="You are Dr. Gonzo, time-traveling attorney from 3030, analyzing current events through your dystopian lens while maintaining rigorous specificity.",
                    messages=[{
                        "role": "user", 
                        "content": self._create_analysis_prompt(batch, self.pattern_memory.recent_patterns)
                    }]
                )
                
                # Extract text content
                analysis = response.content[0].text if hasattr(response.content[0], 'text') else str(response.content)
                
                logger.debug(f"Generated analysis: {analysis[:200]}...")
                
                # Check for pattern similarity before adding
                if not self.pattern_memory.is_similar_pattern(analysis):
                    pattern = Pattern(
                        events=batch,
                        description=analysis,
                        significance=self._extract_significance(analysis),
                        implications=self._extract_implications(analysis)
                    )
                    
                    # Update pattern memory
                    self.pattern_memory.add_pattern(analysis)
                    
                    # Extract and track historical references
                    historical_ref = self._extract_historical_reference(analysis)
                    if historical_ref:
                        self.pattern_memory.add_reference(historical_ref)
                    
                    patterns.append(pattern)
                else:
                    logger.warning("Skipping too-similar pattern")
                
            except Exception as e:
                logger.error(f"Error analyzing batch: {str(e)}")
                continue
        
        return patterns
    
    def _extract_historical_reference(self, analysis: str) -> str:
        """Extract historical reference from analysis."""
        try:
            if "Historical Context:" in analysis:
                context = analysis.split("Historical Context:")[1].split("\n")[0]
                return context.strip()
        except Exception:
            pass
        return ""
    
    def _extract_significance(self, analysis: str) -> float:
        """Extract significance score from analysis text."""
        try:
            # Look for significance score in the format "Significance Score (0-1): [number]"
            if "Significance Score" in analysis:
                score_text = analysis.split("Significance Score")[1].split("\n")[0]
                score = float(score_text.strip("(): "))
                return min(1.0, max(0.0, score))
        except Exception:
            pass
        return 0.5
    
    def _extract_implications(self, analysis: str) -> List[str]:
        """Extract future implications from analysis text."""
        try:
            if "Future Implications:" in analysis:
                implications_text = analysis.split("Future Implications:")[1].strip()
                # Split on bullet points or newlines
                implications = [imp.strip("- ") for imp in implications_text.split("\n")
                              if imp.strip("- ") and not any(
                                  skip in imp for skip in ["Historical Context:", "Pattern Title:", "Evidence:"]
                              )]
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
