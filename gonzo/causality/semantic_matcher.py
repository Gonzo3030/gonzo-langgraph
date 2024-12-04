from typing import List, Tuple, Dict, Any, Optional
from dataclasses import dataclass
from langchain_core.language_models import BaseLLM
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from .types import CausalEvent, EventCategory, EventScope
from .parsers import AnalysisParser

class SemanticMatcher:
    """Matches events based on semantic similarity and causal patterns."""
    
    def __init__(self, llm: Optional[BaseLLM] = None):
        self.llm = llm or ChatAnthropic(
            model="claude-3-opus-20240229",
            temperature=0.1
        )
        self.parser = AnalysisParser()
        
        # Initialize prompts...
        [Previous prompt code remains the same]
    
    async def _analyze_similarity(self, ...) -> SemanticMatch:
        # Get LLM analysis
        response = await self.llm.ainvoke(
            self.match_prompt.format(...)
        )
        
        # Parse response properly now
        analysis = self.parser.parse_similarity_analysis(response.content)
        
        return SemanticMatch(
            event=historical_event,
            similarity_score=analysis.score,
            key_patterns=analysis.patterns,
            reasoning=analysis.reasoning
        )