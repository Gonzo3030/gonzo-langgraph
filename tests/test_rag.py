"""Tests for RAG implementation."""

import pytest
from gonzo.rag.base import MediaAnalysisRAG

# Test content examples
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

def test_pattern_detection(rag_system):
    """Test basic pattern detection."""
    for test_case in TEST_TEXTS:
        # Analyze text
        analysis = rag_system.analyze_text(test_case["text"])
        print(f"\nText: {test_case['text']}")
        print(f"\nAnalysis: {analysis}\n")
        
        # Check that analysis includes expected patterns
        for pattern in test_case["expected_patterns"]:
            assert any(pattern.lower() in part.lower() for part in analysis.split()), \
                f"Expected pattern '{pattern}' not found in analysis. Analysis was: {analysis}"
