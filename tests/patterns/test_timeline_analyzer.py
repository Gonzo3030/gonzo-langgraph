"""Tests for timeline analysis functionality."""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from gonzo.graph.knowledge.graph import KnowledgeGraph
from gonzo.patterns.timeline import TimelineAnalyzer
from gonzo.types import TimeAwareEntity, Property, Relationship

@pytest.fixture
def graph():
    """Create a test knowledge graph."""
    return KnowledgeGraph()

@pytest.fixture
def analyzer(graph):
    """Create a timeline analyzer instance."""
    return TimelineAnalyzer(graph)

def create_test_topic(category: str, timestamp: datetime) -> TimeAwareEntity:
    """Helper to create test topic entities."""
    return TimeAwareEntity(
        type="topic",
        id=uuid4(),
        properties={
            "category": Property(
                key="category",
                value=category,
                timestamp=timestamp
            ),
            "content": Property(
                key="content",
                value=f"Test content for {category}",
                timestamp=timestamp
            )
        },
        valid_from=timestamp
    )

def create_test_relation(source_id, target_id, strength: float, timestamp: datetime) -> Relationship:
    """Helper to create test topic relationships."""
    return Relationship(
        type="topic_relation",
        id=uuid4(),
        source_id=source_id,
        target_id=target_id,
        properties={
            "strength": Property(
                key="strength",
                value=strength,
                timestamp=timestamp
            ),
            "relation_type": Property(
                key="relation_type",
                value="test_relation",
                timestamp=timestamp
            )
        },
        created_at=timestamp
    )

def test_analyze_topic_evolution_empty_graph(analyzer):
    """Test evolution analysis with empty graph."""
    patterns = analyzer.analyze_topic_evolution()
    assert len(patterns) == 0

def test_linear_evolution_pattern(graph, analyzer):
    """Test detection of linear evolution pattern."""
    now = datetime.utcnow()
    
    # Create two related topics
    topic1 = create_test_topic("crypto", now)
    topic2 = create_test_topic("narrative", now + timedelta(minutes=5))
    
    graph.add_entity(topic1)
    graph.add_entity(topic2)
    
    # Add strong relationship
    relation = create_test_relation(
        topic1.id,
        topic2.id,
        strength=0.9,
        timestamp=now + timedelta(minutes=5)
    )
    graph.add_relationship(relation)
    
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
    topic1 = create_test_topic("crypto", now)
    topic2 = create_test_topic("narrative", now + timedelta(minutes=5))
    topic3 = create_test_topic("general", now + timedelta(minutes=10))
    
    graph.add_entity(topic1)
    graph.add_entity(topic2)
    graph.add_entity(topic3)
    
    # Add multiple strong relationships
    rel1 = create_test_relation(topic1.id, topic2.id, 0.8, now + timedelta(minutes=5))
    rel2 = create_test_relation(topic1.id, topic3.id, 0.9, now + timedelta(minutes=10))
    
    graph.add_relationship(rel1)
    graph.add_relationship(rel2)
    
    patterns = analyzer.analyze_topic_evolution()
    
    assert len(patterns) == 1
    pattern = patterns[0]
    assert pattern["evolution_type"] == "branching"
    assert pattern["related_topics"] == 2
    assert 0.84 < pattern["avg_strength"] < 0.86

def test_confidence_threshold_filtering(graph, analyzer):
    """Test that relationships below confidence threshold are filtered."""
    now = datetime.utcnow()
    
    topic1 = create_test_topic("crypto", now)
    topic2 = create_test_topic("narrative", now + timedelta(minutes=5))
    
    graph.add_entity(topic1)
    graph.add_entity(topic2)
    
    # Add weak relationship
    relation = create_test_relation(
        topic1.id,
        topic2.id,
        strength=0.3,  # Below default threshold
        timestamp=now + timedelta(minutes=5)
    )
    graph.add_relationship(relation)
    
    patterns = analyzer.analyze_topic_evolution(min_confidence=0.7)
    assert len(patterns) == 0