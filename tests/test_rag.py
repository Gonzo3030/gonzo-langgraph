"""Tests for RAG implementation."""

import pytest
from gonzo.rag.base import MediaAnalysisRAG

# Test content examples with pattern variations
PATTERN_VARIATIONS = {
    "consensus": ["consensus", "manufacturing consensus", "widespread agreement"],
    "authority": ["authority", "authorities", "unnamed authorities", "appeal to authority"],
    "emotion": ["emotion", "emotional", "fears", "shocking", "troubling"],
}

TEST_TEXTS = [
    {
        "text": """Experts overwhelmingly agree that the new policy measures are necessary for public safety, 
        according to sources familiar with the matter. While some critics have raised concerns, 
        the growing consensus among authorities suggests these measures will be implemented soon.""",
        "expected_patterns": ["consensus", "authority"]
    },
    {
        "text": """Shocking new revelations have emerged as fears grow about potential consequences. 
        Officials claim the situation is under control, but troubling developments continue to surface.""",
        "expected_patterns": ["emotion", "authority"]
    }
]

@pytest.fixture
def rag_system():
    """Create RAG system for testing."""
    return MediaAnalysisRAG()

def pattern_is_present(pattern: str, analysis: str) -> bool:
    """Check if a pattern or its variations are present in the analysis."""
    analysis = analysis.lower()
    variations = PATTERN_VARIATIONS.get(pattern, [pattern])
    return any(variation.lower() in analysis for variation in variations)

def test_pattern_detection(rag_system):
    """Test basic pattern detection."""
    for test_case in TEST_TEXTS:
        # Analyze text
        analysis = rag_system.analyze_text(test_case["text"])
        print(f"\nText: {test_case['text']}")
        print(f"\nAnalysis: {analysis}\n")
        
        # Check that analysis includes expected patterns
        for pattern in test_case["expected_patterns"]:
            assert pattern_is_present(pattern, analysis), \
                f"Expected pattern '{pattern}' (or variations) not found in analysis. \nVariations checked: {PATTERN_VARIATIONS.get(pattern, [pattern])} \nAnalysis was: {analysis}"
