"""Tests for manipulation detection functionality."""

import pytest
from datetime import datetime, timedelta, UTC
from uuid import uuid4

from gonzo.graph.knowledge.graph import KnowledgeGraph
from gonzo.patterns.manipulation import ManipulationDetector
from gonzo.types import TimeAwareEntity, Property, Relationship

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
            "content": f"Crypto market manipulation warning {i}",
            "title": "Market Warning",
            "keywords": ["crypto", "market", "manipulation", "warning"],
            "sentiment": {
                "intensity": 0.7,
                "fear": 0.6,
                "anger": 0.3
            }
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
    assert len(repetition["metadata"]["similarity_scores"]) > 0
    assert all(score > 0.5 for score in repetition["metadata"]["similarity_scores"])

def test_detect_coordinated_shifts():
    """Test detection of coordinated topic shifts."""
    graph = KnowledgeGraph()
    detector = ManipulationDetector(graph)
    
    # Create source entities
    sources = []
    for i in range(3):
        props = {
            "name": f"News Source {i}",
            "type": "media"
        }
        source = graph.add_entity(
            entity_type="media_outlet",
            properties=props
        )
        sources.append(source)
    
    # Create base topic
    now = datetime.now(UTC)
    base_time = now - timedelta(minutes=30)
    base_props = {
        "category": "politics",
        "title": "Initial Political Discussion",
        "content": "Starting point for political narrative",
        "keywords": ["politics", "discussion"],
        "sentiment": {
            "intensity": 0.5,
            "fear": 0.2,
            "anger": 0.1
        }
    }
    base_topic = graph.add_entity(
        entity_type="topic",
        properties=base_props,
        temporal=True,
        valid_from=base_time
    )
    
    # Create coordinated shift pattern
    shift_time = base_time + timedelta(minutes=15)
    target_topics = []
    transitions = []
    
    # Create shift target topics
    for i in range(2):
        props = {
            "category": "politics",
            "title": f"Shifted Narrative {i}",
            "content": "New direction in political discussion",
            "keywords": ["politics", "crisis", "urgent"],
            "sentiment": {
                "intensity": 0.8,
                "fear": 0.7,
                "anger": 0.6
            }
        }
        target = graph.add_entity(
            entity_type="topic",
            properties=props,
            temporal=True,
            valid_from=shift_time
        )
        target_topics.append(target)
    
    # Create transitions from each source
    for i, source in enumerate(sources):
        target = target_topics[i % len(target_topics)]
        trans = graph.add_relationship(
            source_id=base_topic.id,
            target_id=target.id,
            rel_type="topic_transition",
            metadata={"source_entity_id": source.id},
            temporal=True,
            valid_from=shift_time + timedelta(seconds=i*30)  # Slightly staggered but coordinated
        )
        transitions.append(trans)
    
    # Test pattern detection
    patterns = detector.detect_narrative_manipulation(timeframe=3600)
    
    # Find coordinated shift pattern
    shifts = [p for p in patterns if p["pattern_type"] == "coordinated_shift"]
    assert len(shifts) == 1
    
    shift = shifts[0]
    assert shift["topic_id"] == str(base_topic.id)
    assert shift["confidence"] > 0.6
    assert len(shift["metadata"]["clusters"]) == 1
    
    cluster = shift["metadata"]["clusters"][0]
    assert cluster["source_count"] == len(sources)
    assert cluster["transition_count"] >= 3
    assert cluster["shared_target_count"] >= 1

def test_detect_emotional_manipulation():
    """Test detection of emotional manipulation patterns."""
    graph = KnowledgeGraph()
    detector = ManipulationDetector(graph)
    
    # Create escalating emotional content
    now = datetime.now(UTC)
    base_time = now - timedelta(minutes=30)
    topics = []
    
    # Create sequence of topics with escalating emotion
    for i in range(4):
        intensity = 0.5 + (i * 0.1)
        fear = 0.3 + (i * 0.15)
        anger = 0.2 + (i * 0.2)
        
        props = {
            "category": "health",
            "title": f"Health Crisis Update {i}",
            "content": f"Escalating health situation report {i}",
            "keywords": ["health", "crisis", "urgent", "warning"],
            "sentiment": {
                "intensity": intensity,
                "fear": fear,
                "anger": anger,
                "joy": 0.1,
                "sadness": 0.4
            }
        }
        
        topic = graph.add_entity(
            entity_type="topic",
            properties=props,
            temporal=True,
            valid_from=base_time + timedelta(minutes=i*10)
        )
        topics.append(topic)
    
    # Test pattern detection
    patterns = detector.detect_narrative_manipulation(timeframe=3600)
    
    # Find emotional manipulation pattern
    emotional = [p for p in patterns if p["pattern_type"] == "emotional_manipulation"]
    assert len(emotional) >= 1
    
    pattern = emotional[0]
    assert pattern["topic_id"] == str(topics[-1].id)  # Should detect pattern on latest topic
    assert pattern["confidence"] > 0.7
    
    metadata = pattern["metadata"]
    assert metadata["escalation_count"] > 0
    assert metadata["max_escalation"] > 0
    assert metadata["fear_level"] > 0.6
    assert metadata["anger_level"] > 0.6

def test_no_emotional_manipulation_stable_content():
    """Test that stable emotional content doesn't trigger manipulation detection."""
    graph = KnowledgeGraph()
    detector = ManipulationDetector(graph)
    
    # Create topics with stable emotional content
    now = datetime.now(UTC)
    base_time = now - timedelta(minutes=30)
    
    for i in range(3):
        props = {
            "category": "tech",
            "title": f"Technology Update {i}",
            "content": "Regular technology news update",
            "keywords": ["technology", "update", "news"],
            "sentiment": {
                "intensity": 0.4,
                "fear": 0.2,
                "anger": 0.1,
                "joy": 0.3,
                "sadness": 0.1
            }
        }
        
        graph.add_entity(
            entity_type="topic",
            properties=props,
            temporal=True,
            valid_from=base_time + timedelta(minutes=i*10)
        )
    
    # Test pattern detection
    patterns = detector.detect_narrative_manipulation(timeframe=3600)
    
    # Should not find emotional manipulation
    emotional = [p for p in patterns if p["pattern_type"] == "emotional_manipulation"]
    assert len(emotional) == 0

def test_no_coordinated_shifts_random_transitions():
    """Test that random, uncoordinated transitions don't trigger shift detection."""
    graph = KnowledgeGraph()
    detector = ManipulationDetector(graph)
    
    # Create base topic
    now = datetime.now(UTC)
    base_time = now - timedelta(minutes=30)
    base_props = {
        "category": "tech",
        "title": "Tech Discussion",
        "content": "Technology discussion base",
        "keywords": ["technology", "discussion"]
    }
    base_topic = graph.add_entity(
        entity_type="topic",
        properties=base_props,
        temporal=True,
        valid_from=base_time
    )
    
    # Create random transitions over time
    for i in range(3):
        # Different times
        shift_time = base_time + timedelta(minutes=i*20)
        
        # Create target topic
        target_props = {
            "category": "tech",
            "title": f"New Tech Topic {i}",
            "content": "Technology discussion continuation",
            "keywords": ["technology", "discussion", str(i)]
        }
        target = graph.add_entity(
            entity_type="topic",
            properties=target_props,
            temporal=True,
            valid_from=shift_time
        )
        
        # Create transition
        graph.add_relationship(
            source_id=base_topic.id,
            target_id=target.id,
            rel_type="topic_transition",
            temporal=True,
            valid_from=shift_time
        )
    
    # Test pattern detection
    patterns = detector.detect_narrative_manipulation(timeframe=3600)
    
    # Should not find coordinated shifts
    shifts = [p for p in patterns if p["pattern_type"] == "coordinated_shift"]
    assert len(shifts) == 0

def test_topics_outside_timeframe():
    """Test that old topics are excluded from analysis."""
    graph = KnowledgeGraph()
    detector = ManipulationDetector(graph)
    
    # Create old topic
    now = datetime.now(UTC)
    old_time = now - timedelta(hours=2)
    
    props = {
        "category": "crypto",
        "content": "Old crypto content",
        "sentiment": {
            "intensity": 0.8,
            "fear": 0.7,
            "anger": 0.6
        }
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
