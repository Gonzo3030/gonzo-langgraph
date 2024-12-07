"""Tests for contextual learning and power structure mapping."""

import pytest
from datetime import datetime, UTC

from gonzo.patterns.contextual import (
    ContextualPatternDetector, KnowledgeClaim,
    ConfidenceLevel, PowerStructure
)

@pytest.fixture
def detector():
    """Initialize detector with basic setup."""
    detector = ContextualPatternDetector()
    # Add some initial entities for testing
    power = detector.power_structure
    power.add_entity(
        id="media_corp",
        name="Media Corporation",
        entity_type="media_outlet",
        properties={
            "type": "broadcast",
            "reach": "national"
        }
    )
    power.add_entity(
        id="politician",
        name="Test Politician",
        entity_type="individual",
        properties={
            "role": "senator",
            "party": "independent"
        }
    )
    return detector

def test_learn_new_entity(detector):
    """Test learning about a new entity."""
    detector.learn_from_source(
        source_type="financial_report",
        content={
            "entities": [{
                "id": "corp_1",
                "name": "Corporation One",
                "type": "organization",
                "properties": {
                    "industry": "pharma",
                    "market_cap": "high"
                }
            }]
        },
        confidence=0.8
    )
    
    # Verify entity was added
    entity = detector.power_structure.entities.get("corp_1")
    assert entity is not None
    assert entity.properties["industry"].value == "pharma"
    assert entity.properties["industry"].confidence == 0.8

def test_update_existing_entity(detector):
    """Test updating information about an existing entity."""
    # First update
    detector.learn_from_source(
        source_type="news_report",
        content={
            "entities": [{
                "id": "media_corp",
                "properties": {
                    "bias": "corporate"
                }
            }]
        },
        confidence=0.7
    )
    
    # Second update with higher confidence
    detector.learn_from_source(
        source_type="academic_study",
        content={
            "entities": [{
                "id": "media_corp",
                "properties": {
                    "bias": "establishment"
                }
            }]
        },
        confidence=0.9
    )
    
    entity = detector.power_structure.entities["media_corp"]
    assert entity.properties["bias"].value == "establishment"
    assert entity.properties["bias"].confidence == 0.9

def test_learn_influence_relationship(detector):
    """Test learning about influence relationships."""
    detector.learn_from_source(
        source_type="investigation",
        content={
            "relationships": [{
                "source": "media_corp",
                "target": "politician",
                "type": "influences",
                "influence": {
                    "strength": 0.8
                }
            }]
        },
        confidence=0.75
    )
    
    # Check influence network
    influence = detector.power_structure.influence_networks
    assert "media_corp" in influence
    assert "politician" in influence["media_corp"]
    assert influence["media_corp"]["politician"] == 0.8 * 0.75  # strength * confidence

def test_learn_financial_relationship(detector):
    """Test learning about financial relationships."""
    detector.learn_from_source(
        source_type="financial_disclosure",
        content={
            "relationships": [{
                "source": "media_corp",
                "target": "politician",
                "type": "supports",
                "financial": {
                    "type": "donation",
                    "amount": 50000,
                    "year": 2024
                }
            }]
        },
        confidence=0.95
    )
    
    financial = detector.power_structure.financial_relationships
    assert "media_corp" in financial
    assert "politician" in financial["media_corp"]
    assert financial["media_corp"]["politician"].value["amount"] == 50000
    assert financial["media_corp"]["politician"].confidence == 0.95

def test_learn_policy_alignment(detector):
    """Test learning about policy alignments."""
    detector.learn_from_source(
        source_type="voting_records",
        content={
            "relationships": [{
                "source": "media_corp",
                "target": "politician",
                "type": "aligns",
                "policy_alignment": {
                    "score": 0.85,
                    "topics": ["media_regulation", "corporate_tax"]
                }
            }]
        },
        confidence=0.9
    )
    
    alignments = detector.power_structure.policy_alignments
    assert "media_corp" in alignments
    assert "politician" in alignments["media_corp"]
    assert alignments["media_corp"]["politician"] == 0.85
    # Check reverse relationship
    assert alignments["politician"]["media_corp"] == 0.85

def test_corroboration_increases_confidence(detector):
    """Test that corroborating evidence increases confidence."""
    # Initial information
    detector.learn_from_source(
        source_type="news_report",
        content={
            "entities": [{
                "id": "media_corp",
                "properties": {
                    "bias": "corporate"
                }
            }]
        },
        confidence=0.6
    )
    
    initial_confidence = detector.power_structure.entities["media_corp"].properties["bias"].confidence
    
    # Corroborating information
    detector.learn_from_source(
        source_type="academic_study",
        content={
            "entities": [{
                "id": "media_corp",
                "properties": {
                    "bias": "corporate"
                }
            }]
        },
        confidence=0.5
    )
    
    final_confidence = detector.power_structure.entities["media_corp"].properties["bias"].confidence
    assert final_confidence > initial_confidence

def test_knowledge_claim_creation():
    """Test creation and updating of knowledge claims."""
    claim = KnowledgeClaim(
        value="test value",
        source="test source",
        confidence=0.7
    )
    
    assert claim.value == "test value"
    assert claim.source == "test source"
    assert claim.confidence == 0.7
    assert len(claim.corroborations) == 0
    
    # Add corroboration
    claim.add_corroboration("new source", 0.6)
    assert len(claim.corroborations) == 1
    assert claim.confidence > 0.7  # Should increase with corroboration