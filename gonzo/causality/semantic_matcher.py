from typing import List, Tuple, Dict, Any, Optional
from dataclasses import dataclass
from langchain_core.language_models import BaseLLM
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from .types import CausalEvent, EventCategory, EventScope
from .parsers import AnalysisParser

@dataclass
class SemanticMatch:
    """Represents a semantic match between events."""
    event: CausalEvent
    similarity_score: float
    key_patterns: List[str]
    reasoning: str

class SemanticMatcher:
    """Matches events based on semantic similarity and causal patterns."""
    
    def __init__(self, llm: Optional[BaseLLM] = None):
        self.llm = llm or ChatAnthropic(
            model="claude-3-opus-20240229",
            temperature=0.1
        )
        self.parser = AnalysisParser()
        
        self.match_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert at analyzing causal relationships and patterns in events."),
            ("user", "Compare the following events and assess their similarity:\n\nEvent 1: {event1}\nEvent 2: {event2}\n\nAnalyze their causal patterns, key actors, and potential relationships.")
        ])
    
    async def _analyze_similarity(self, event1: CausalEvent, event2: CausalEvent) -> SemanticMatch:
        """Analyze semantic similarity between two events.
        
        Args:
            event1: First event to compare
            event2: Second event to compare
            
        Returns:
            Semantic match analysis
        """
        # Get LLM analysis
        response = await self.llm.ainvoke(
            self.match_prompt.format(
                event1=str(event1),
                event2=str(event2)
            )
        )
        
        # Parse response
        analysis = self.parser.parse_similarity_analysis(response.content)
        
        return SemanticMatch(
            event=event1,
            similarity_score=analysis.score,
            key_patterns=analysis.patterns,
            reasoning=analysis.reasoning
        )