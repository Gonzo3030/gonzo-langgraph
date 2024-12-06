"""Tests for timeline analysis functionality."""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from gonzo.graph.knowledge.graph import KnowledgeGraph
from gonzo.patterns.timeline import TimelineAnalyzer

@pytest.fixture
def graph():
    """Create a test knowledge graph."""
    return KnowledgeGraph()

@pytest.fixture
def analyzer(graph):
    """Create a timeline analyzer instance."""
    return TimelineAnalyzer(graph)

def create_test_topic(category: str, timestamp: datetime):
    """Helper to create test topic entities."""
    properties = {
        "category": category,
        "content": f"Test content for {category}"
    }
    return "topic", properties, True, timestamp, None

def create_test_relation(source_id, target_id, strength: float, timestamp: datetime):
    """Helper to create test topic relationships."""
    properties = {
        "strength": strength,
        "relation_type": "test_relation"
    }
    return "topic_relation", source_id, target_id, properties

def test_analyze_topic_evolution_empty_graph(analyzer):
    """Test evolution analysis with empty graph."""
    patterns = analyzer.analyze_topic_evolution()
    assert len(patterns) == 0

def test_linear_evolution_pattern(graph, analyzer):
    """Test detection of linear evolution pattern."""
    now = datetime.utcnow()
    
    # Create two related topics
    type1, props1, temporal1, valid_from1, valid_to1 = create_test_topic("crypto", now)
    topic1 = graph.add_entity(type1, props1, temporal1, valid_from1, valid_to1)
    
    type2, props2, temporal2, valid_from2, valid_to2 = create_test_topic("narrative", now + timedelta(minutes=5))
    topic2 = graph.add_entity(type2, props2, temporal2, valid_from2, valid_to2)
    
    # Add strong relationship
    rel_type, src, tgt, props = create_test_relation(
        topic1.id, topic2.id, 0.9,
        now + timedelta(minutes=5)
    )
    graph.add_relationship(rel_type, src, tgt, props)
    
    # Analyze evolution
    patterns = analyzer.analyze_topic_evolution(timeframe=3600)
    
    assert len(patterns) == 1
    pattern = patterns[0]
    assert pattern["pattern_type"] == "topic_evolution"
    assert pattern["topic_id"] == topic1.id
    assert pattern["related_topics"] == 1
    assert pattern["evolution_type"] == "linear"
    assert pattern["avg_strength"] == 0.9

def test_branching_evolution_pattern(graph, analyzer):
    """Test detection of branching evolution pattern."""
    now = datetime.utcnow()
    
    # Create topic with multiple strong relationships
    type1, props1, temporal1, valid_from1, valid_to1 = create_test_topic("crypto", now)
    topic1 = graph.add_entity(type1, props1, temporal1, valid_from1, valid_to1)
    
    type2, props2, temporal2, valid_from2, valid_to2 = create_test_topic("narrative", now + timedelta(minutes=5))
    topic2 = graph.add_entity(type2, props2, temporal2, valid_from2, valid_to2)
    
    type3, props3, temporal3, valid_from3, valid_to3 = create_test_topic("general", now + timedelta(minutes=10))
    topic3 = graph.add_entity(type3, props3, temporal3, valid_from3, valid_to3)
    
    # Add multiple strong relationships
    rel_type1, src1, tgt1, props1 = create_test_relation(
        topic1.id, topic2.id, 0.8,
        now + timedelta(minutes=5)
    )
    graph.add_relationship(rel_type1, src1, tgt1, props1)
    
    rel_type2, src2, tgt2, props2 = create_test_relation(
        topic1.id, topic3.id, 0.9,
        now + timedelta(minutes=10)
    )
    graph.add_relationship(rel_type2, src2, tgt2, props2)
    
    patterns = analyzer.analyze_topic_evolution()
    
    assert len(patterns) == 1
    pattern = patterns[0]
    assert pattern["evolution_type"] == "branching"
    assert pattern["related_topics"] == 2
    assert 0.84 < pattern["avg_strength"] < 0.86

def test_confidence_threshold_filtering(graph, analyzer):
    """Test that relationships below confidence threshold are filtered."""
    now = datetime.utcnow()
    
    type1, props1, temporal1, valid_from1, valid_to1 = create_test_topic("crypto", now)
    topic1 = graph.add_entity(type1, props1, temporal1, valid_from1, valid_to1)
    
    type2, props2, temporal2, valid_from2, valid_to2 = create_test_topic("narrative", now + timedelta(minutes=5))
    topic2 = graph.add_entity(type2, props2, temporal2, valid_from2, valid_to2)
    
    # Add weak relationship
    rel_type, src, tgt, props = create_test_relation(
        topic1.id, topic2.id, 0.3,  # Below default threshold
        now + timedelta(minutes=5)
    )
    graph.add_relationship(rel_type, src, tgt, props)
    
    patterns = analyzer.analyze_topic_evolution(min_confidence=0.7)
    assert len(patterns) == 0