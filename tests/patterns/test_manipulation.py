"""Tests for manipulation detection functionality."""

import pytest
from datetime import datetime, timedelta, UTC
from uuid import uuid4

from gonzo.graph.knowledge.graph import KnowledgeGraph
from gonzo.patterns.manipulation import ManipulationDetector
from gonzo.types import TimeAwareEntity, Property

def test_detect_narrative_manipulation_empty_graph():
    """Test manipulation detection with empty graph."""
    graph = KnowledgeGraph()
    detector = ManipulationDetector(graph)
    
    patterns = detector.detect_narrative_manipulation()
    assert len(patterns) == 0

def test_detect_narrative_repetition():
    """Test detection of repeated narratives."""
    graph = KnowledgeGraph()
    detector = ManipulationDetector(graph)
    
    # Create test topics in same category
    now = datetime.now(UTC)
    base_time = now - timedelta(minutes=30)
    
    topics = []
    for i in range(3):
        topic_time = base_time + timedelta(minutes=i*10)
        props = {
            "category": "crypto",
            "content": f"Test content {i} about crypto"
        }
        topic = graph.add_entity(
            entity_type="topic",
            properties=props,
            temporal=True,
            valid_from=topic_time
        )
        topics.append(topic)
    
    # Test pattern detection
    patterns = detector.detect_narrative_manipulation(timeframe=3600)
    
    assert len(patterns) >= 1
    repetition = next(p for p in patterns if p["pattern_type"] == "narrative_repetition")
    assert repetition["category"] == "crypto"
    assert repetition["topic_count"] == 3
    assert repetition["confidence"] >= 0.7
    assert str(topics[0].id) == repetition["metadata"]["base_topic_id"]
    
def test_no_repetition_different_categories():
    """Test that topics in different categories aren't flagged as repetition."""
    graph = KnowledgeGraph()
    detector = ManipulationDetector(graph)
    
    # Create test topics in different categories
    now = datetime.now(UTC)
    base_time = now - timedelta(minutes=30)
    
    categories = ["crypto", "politics", "tech"]
    for i, category in enumerate(categories):
        topic_time = base_time + timedelta(minutes=i*10)
        props = {
            "category": category,
            "content": f"Test content about {category}"
        }
        graph.add_entity(
            entity_type="topic",
            properties=props,
            temporal=True,
            valid_from=topic_time
        )
    
    # Test pattern detection
    patterns = detector.detect_narrative_manipulation(timeframe=3600)
    
    # Should not detect repetition since topics are in different categories
    repetition_patterns = [p for p in patterns if p["pattern_type"] == "narrative_repetition"]
    assert len(repetition_patterns) == 0

def test_topics_outside_timeframe():
    """Test that old topics are excluded from analysis."""
    graph = KnowledgeGraph()
    detector = ManipulationDetector(graph)
    
    # Create old topic
    now = datetime.now(UTC)
    old_time = now - timedelta(hours=2)
    
    props = {
        "category": "crypto",
        "content": "Old crypto content"
    }
    graph.add_entity(
        entity_type="topic",
        properties=props,
        temporal=True,
        valid_from=old_time
    )
    
    # Test with 1 hour timeframe
    patterns = detector.detect_narrative_manipulation(timeframe=3600)
    
    # Should not detect any patterns since topic is outside timeframe
    assert len(patterns) == 0