"""Tests for pattern detection functionality."""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from gonzo.graph.knowledge.graph import KnowledgeGraph
from gonzo.patterns.detector import PatternDetector

@pytest.fixture
def graph():
    """Create a test knowledge graph."""
    return KnowledgeGraph()

@pytest.fixture
def detector(graph):
    """Create a pattern detector instance."""
    return PatternDetector(graph)

def create_topic_entity(category: str, timestamp: datetime):
    """Helper to create topic entities."""
    properties = {
        "category": category,
        "content": f"Test content for {category}"
    }
    return "topic", properties, True, timestamp, None

def create_transition(source_id, target_id, timestamp: datetime, from_cat: str, to_cat: str):
    """Helper to create transition relationships."""
    properties = {
        "transition_time": 0.5,
        "from_category": from_cat,
        "to_category": to_cat
    }
    return "topic_transition", source_id, target_id, properties

def test_detect_topic_cycles_empty_graph(detector):
    """Test cycle detection with empty graph."""
    cycles = detector.detect_topic_cycles()
    assert len(cycles) == 0

def test_detect_simple_cycle(graph, detector):
    """Test detection of a simple topic cycle."""
    # Create topic sequence: crypto -> narrative -> crypto
    now = datetime.utcnow()
    
    # Create entities
    type1, props1, temporal1, valid_from1, valid_to1 = create_topic_entity("crypto", now)
    topic1 = graph.add_entity(type1, props1, temporal1, valid_from1, valid_to1)
    
    type2, props2, temporal2, valid_from2, valid_to2 = create_topic_entity("narrative", now + timedelta(minutes=5))
    topic2 = graph.add_entity(type2, props2, temporal2, valid_from2, valid_to2)
    
    type3, props3, temporal3, valid_from3, valid_to3 = create_topic_entity("crypto", now + timedelta(minutes=10))
    topic3 = graph.add_entity(type3, props3, temporal3, valid_from3, valid_to3)
    
    # Add transitions
    rel_type1, src1, tgt1, props1 = create_transition(
        topic1.id, topic2.id, now + timedelta(minutes=5),
        "crypto", "narrative"
    )
    graph.add_relationship(rel_type1, src1, tgt1, props1)
    
    rel_type2, src2, tgt2, props2 = create_transition(
        topic2.id, topic3.id, now + timedelta(minutes=10),
        "narrative", "crypto"
    )
    graph.add_relationship(rel_type2, src2, tgt2, props2)
    
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
    
    # Create entities
    type1, props1, temporal1, valid_from1, valid_to1 = create_topic_entity("crypto", now)
    topic1 = graph.add_entity(type1, props1, temporal1, valid_from1, valid_to1)
    
    type2, props2, temporal2, valid_from2, valid_to2 = create_topic_entity("narrative", now + timedelta(minutes=5))
    topic2 = graph.add_entity(type2, props2, temporal2, valid_from2, valid_to2)
    
    type3, props3, temporal3, valid_from3, valid_to3 = create_topic_entity("general", now + timedelta(minutes=10))
    topic3 = graph.add_entity(type3, props3, temporal3, valid_from3, valid_to3)
    
    # Add transitions
    rel_type1, src1, tgt1, props1 = create_transition(
        topic1.id, topic2.id, now + timedelta(minutes=5),
        "crypto", "narrative"
    )
    graph.add_relationship(rel_type1, src1, tgt1, props1)
    
    rel_type2, src2, tgt2, props2 = create_transition(
        topic2.id, topic3.id, now + timedelta(minutes=10),
        "narrative", "general"
    )
    graph.add_relationship(rel_type2, src2, tgt2, props2)
    
    cycles = detector.detect_topic_cycles(timeframe=3600)
    assert len(cycles) == 0

def test_cycle_outside_timeframe(graph, detector):
    """Test that cycles outside timeframe are not detected."""
    now = datetime.utcnow()
    
    # Create entities with long time gaps
    type1, props1, temporal1, valid_from1, valid_to1 = create_topic_entity("crypto", now)
    topic1 = graph.add_entity(type1, props1, temporal1, valid_from1, valid_to1)
    
    type2, props2, temporal2, valid_from2, valid_to2 = create_topic_entity("narrative", now + timedelta(hours=2))
    topic2 = graph.add_entity(type2, props2, temporal2, valid_from2, valid_to2)
    
    type3, props3, temporal3, valid_from3, valid_to3 = create_topic_entity("crypto", now + timedelta(hours=4))
    topic3 = graph.add_entity(type3, props3, temporal3, valid_from3, valid_to3)
    
    # Add transitions
    rel_type1, src1, tgt1, props1 = create_transition(
        topic1.id, topic2.id, now + timedelta(hours=2),
        "crypto", "narrative"
    )
    graph.add_relationship(rel_type1, src1, tgt1, props1)
    
    rel_type2, src2, tgt2, props2 = create_transition(
        topic2.id, topic3.id, now + timedelta(hours=4),
        "narrative", "crypto"
    )
    graph.add_relationship(rel_type2, src2, tgt2, props2)
    
    # Use 1 hour timeframe
    cycles = detector.detect_topic_cycles(timeframe=3600)
    assert len(cycles) == 0