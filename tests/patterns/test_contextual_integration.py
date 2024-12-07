"""Tests for integrated contextual pattern detection functionality."""

import pytest
from datetime import datetime, UTC, timedelta
from unittest.mock import Mock, patch

from gonzo.patterns.contextual import ContextualPatternDetector
from gonzo.state_management.api_state import APIState
from gonzo.memory.vector_store import VectorStoreMemory
from gonzo.memory.timeline import Timeline

@pytest.fixture
def sample_media_content():
    """Sample content about media manipulation."""
    return {
        "entities": [
            {
                "id": "media_corp",
                "name": "Major Media Corp",
                "type": "media_outlet",
                "properties": {
                    "type": "broadcast",
                    "reach": "national",
                    "bias": "establishment"
                }
            },
            {
                "id": "pharma_co",
                "name": "Big Pharma Inc",
                "type": "organization",
                "properties": {
                    "industry": "pharmaceutical",
                    "market_cap": "high",
                    "regulatory_status": "under_investigation"
                }
            }
        ],
        "relationships": [
            {
                "source": "media_corp",
                "target": "pharma_co",
                "type": "supports",
                "financial": {
                    "type": "advertising",
                    "amount": 1000000,
                    "year": 2024
                },
                "influence": {
                    "strength": 0.8,
                    "channel": "narrative_control"
                }
            }
        ]
    }

@pytest.fixture
def detector():
    """Initialize detector with mocked dependencies."""
    with patch('gonzo.persistence.checkpointer.Checkpointer') as mock_checkpointer:
        detector = ContextualPatternDetector()
        detector.checkpointer = mock_checkpointer()
        return detector

def test_integrated_learning(detector, sample_media_content):
    """Test integrated learning from a media source."""
    # Learn from source
    detector.learn_from_source(
        source_type="investigative_report",
        content=sample_media_content,
        confidence=0.9
    )
    
    # Check power structure
    media = detector.power_structure.entities.get("media_corp")
    pharma = detector.power_structure.entities.get("pharma_co")
    
    assert media is not None
    assert pharma is not None
    assert media.properties["bias"].value == "establishment"
    assert media.properties["bias"].confidence == 0.9
    
    # Check vector memory
    memories = detector.vector_memory.get_relevant_memories(
        "media bias establishment",
        k=1
    )
    assert len(memories) > 0
    assert "establishment" in memories[0]["text"]
    
    # Check timeline
    events = detector.timeline.get_events()
    assert any(e["type"] == "entity_created" and e["entity_id"] == "media_corp" for e in events)
    assert any(e["type"] == "relationship_created" for e in events)

def test_relationship_tracking(detector, sample_media_content):
    """Test tracking of complex relationships."""
    detector.learn_from_source(
        source_type="investigative_report",
        content=sample_media_content,
        confidence=0.9
    )
    
    # Check influence network
    influence = detector.power_structure.influence_networks
    assert "media_corp" in influence
    assert "pharma_co" in influence["media_corp"]
    assert influence["media_corp"]["pharma_co"] == 0.8 * 0.9  # strength * confidence
    
    # Check financial relationships
    financials = detector.power_structure.financial_relationships
    assert "media_corp" in financials
    assert "pharma_co" in financials["media_corp"]
    assert financials["media_corp"]["pharma_co"].value["amount"] == 1000000

def test_checkpointing(detector, sample_media_content):
    """Test state persistence through checkpoints."""
    # Learn initial content
    detector.learn_from_source(
        source_type="investigative_report",
        content=sample_media_content,
        confidence=0.9
    )
    
    # Verify checkpoint was saved
    detector.checkpointer.save.assert_called()
    call_args = detector.checkpointer.save.call_args[0][0]
    
    assert "power_structure" in call_args
    assert "timeline" in call_args
    assert "state" in call_args

def test_vector_search_integration(detector):
    """Test integration with vector store for pattern search."""
    # Add some test patterns
    detector.learn_from_source(
        source_type="news_analysis",
        content={
            "entities": [{
                "id": "media_org",
                "type": "media_outlet",
                "properties": {
                    "pattern": "Uses fear tactics in reporting",
                    "evidence": "Consistent catastrophic framing"
                }
            }]
        },
        confidence=0.8
    )
    
    # Search for patterns
    results = detector.search_patterns("fear tactics media reporting")
    
    assert len(results) > 0
    assert any("fear tactics" in r["text"].lower() for r in results)

def test_timeline_integration(detector, sample_media_content):
    """Test integration with timeline tracking."""
    start_time = datetime.now(UTC)
    
    # Add content in sequence
    detector.learn_from_source(
        source_type="initial_report",
        content={"entities": [sample_media_content["entities"][0]]},
        confidence=0.7
    )
    
    detector.learn_from_source(
        source_type="follow_up",
        content={"entities": [sample_media_content["entities"][1]]},
        confidence=0.8
    )
    
    # Check timeline
    events = detector.timeline.get_events()
    
    # Verify event sequence
    assert len(events) >= 2
    for event in events:
        assert event["timestamp"] >= start_time
        assert "type" in event
        assert "timestamp" in event

def test_state_management_integration(detector):
    """Test integration with API state management."""
    initial_state = detector.state.to_dict()
    
    # Perform some operations
    detector.learn_from_source(
        source_type="test",
        content={"entities": [{"id": "test", "type": "test"}]},
        confidence=0.5
    )
    
    # State should be updated and checkpointed
    updated_state = detector.state.to_dict()
    assert initial_state != updated_state
    detector.checkpointer.save.assert_called()