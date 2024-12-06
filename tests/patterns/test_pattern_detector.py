"""Tests for pattern detection functionality."""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from gonzo.graph.knowledge.graph import KnowledgeGraph
from gonzo.patterns.detector import PatternDetector
from gonzo.types import TimeAwareEntity, Property, Relationship

@pytest.fixture
def graph():
    """Create a test knowledge graph."""
    return KnowledgeGraph()

@pytest.fixture
def detector(graph):
    """Create a pattern detector instance."""
    return PatternDetector(graph)

def create_topic_entity(category: str, timestamp: datetime) -> TimeAwareEntity:
    """Helper to create topic entities."""
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

def create_transition(source_id, target_id, timestamp: datetime) -> Relationship:
    """Helper to create transition relationships."""
    return Relationship(
        type="topic_transition",
        id=uuid4(),
        source_id=source_id,
        target_id=target_id,
        properties={
            "transition_time": Property(
                key="transition_time",
                value=0.5,
                timestamp=timestamp
            )
        },
        created_at=timestamp
    )

def test_detect_topic_cycles_empty_graph(detector):
    """Test cycle detection with empty graph."""
    cycles = detector.detect_topic_cycles()
    assert len(cycles) == 0

def test_detect_simple_cycle(graph, detector):
    """Test detection of a simple topic cycle."""
    # Create topic sequence: crypto -> narrative -> crypto
    now = datetime.utcnow()
    
    topic1 = create_topic_entity("crypto", now)
    topic2 = create_topic_entity("narrative", now + timedelta(minutes=5))
    topic3 = create_topic_entity("crypto", now + timedelta(minutes=10))
    
    graph.add_entity(topic1)
    graph.add_entity(topic2)
    graph.add_entity(topic3)
    
    # Add transitions
    trans1 = create_transition(topic1.id, topic2.id, now + timedelta(minutes=5))
    trans2 = create_transition(topic2.id, topic3.id, now + timedelta(minutes=10))
    
    graph.add_relationship(trans1)
    graph.add_relationship(trans2)
    
    # Detect cycles
    cycles = detector.detect_topic_cycles(timeframe=3600)
    
    assert len(cycles) == 1
    cycle = cycles[0]
    assert cycle["pattern_type"] == "topic_cycle"
    assert cycle["start_category"] == "crypto"
    assert set(cycle["categories"]) == {"crypto", "narrative"}
    assert cycle["length"] == 2

def test_no_cycle_different_topics(graph, detector):
    """Test with different topics that don't form a cycle."""
    now = datetime.utcnow()
    
    topic1 = create_topic_entity("crypto", now)
    topic2 = create_topic_entity("narrative", now + timedelta(minutes=5))
    topic3 = create_topic_entity("general", now + timedelta(minutes=10))
    
    graph.add_entity(topic1)
    graph.add_entity(topic2)
    graph.add_entity(topic3)
    
    trans1 = create_transition(topic1.id, topic2.id, now + timedelta(minutes=5))
    trans2 = create_transition(topic2.id, topic3.id, now + timedelta(minutes=10))
    
    graph.add_relationship(trans1)
    graph.add_relationship(trans2)
    
    cycles = detector.detect_topic_cycles(timeframe=3600)
    assert len(cycles) == 0

def test_cycle_outside_timeframe(graph, detector):
    """Test that cycles outside timeframe are not detected."""
    now = datetime.utcnow()
    
    topic1 = create_topic_entity("crypto", now)
    topic2 = create_topic_entity("narrative", now + timedelta(hours=2))
    topic3 = create_topic_entity("crypto", now + timedelta(hours=4))
    
    graph.add_entity(topic1)
    graph.add_entity(topic2)
    graph.add_entity(topic3)
    
    trans1 = create_transition(topic1.id, topic2.id, now + timedelta(hours=2))
    trans2 = create_transition(topic2.id, topic3.id, now + timedelta(hours=4))
    
    graph.add_relationship(trans1)
    graph.add_relationship(trans2)
    
    # Use 1 hour timeframe
    cycles = detector.detect_topic_cycles(timeframe=3600)
    assert len(cycles) == 0