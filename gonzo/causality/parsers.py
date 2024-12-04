from typing import List, Tuple, Dict
import re
from dataclasses import dataclass

@dataclass
class SimilarityAnalysis:
    score: float
    patterns: List[str]
    reasoning: str

class AnalysisParser:
    """Parses LLM responses into structured analysis."""
    
    @staticmethod
    def parse_similarity_analysis(text: str) -> SimilarityAnalysis:
        """Parse similarity analysis from LLM response."""
        # Extract similarity score
        score_match = re.search(r'Similarity[\s:]+(\d+(?:\.\d+)?)', text)
        score = float(score_match.group(1)) if score_match else 0.0
        
        # Extract patterns
        patterns = []
        pattern_section = re.search(r'Key Patterns:[\n\r]+((?:[^\n]+[\n\r]+)*)', text)
        if pattern_section:
            pattern_text = pattern_section.group(1)
            patterns = [p.strip('- ').strip() 
                       for p in pattern_text.split('\n') 
                       if p.strip('- ').strip()]
        
        # Extract reasoning
        reasoning_section = re.search(r'Reasoning:[\n\r]+((?:[^\n]+[\n\r]+)*)', text)
        reasoning = reasoning_section.group(1).strip() if reasoning_section else ""
        
        return SimilarityAnalysis(
            score=score,
            patterns=patterns,
            reasoning=reasoning
        )
    
    @staticmethod
    def format_response(
        current: str,
        historical: str,
        analysis: SimilarityAnalysis
    ) -> str:
        """Format analysis for Gonzo-style response."""
        return f"""*adjusts time-goggles, peers through the mists of history*

Hold onto your reality tunnels, because this ain't just déjà vu - we're seeing a {analysis.score*100:.1f}% match with the ghosts of chaos past.

Current situation: {current}

This mirrors what we saw back when: {historical}

The patterns are screaming at us:
{chr(10).join(f'- {p}' for p in analysis.patterns)}

And let me tell you why this matters: {analysis.reasoning}

*takes long drag from cyber-cigarette*

Ignore these parallels at your own peril, you beautiful doom-magnets."""
