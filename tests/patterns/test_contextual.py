"""Tests for contextual pattern detection."""

import pytest
from datetime import datetime, UTC

from gonzo.patterns.contextual import (
    Entity, PowerStructure, ContextualPatternDetector
)

@pytest.fixture
def detector():
    """Initialize detector with basic knowledge base."""
    detector = ContextualPatternDetector()
    detector.initialize_knowledge_base()
    return detector

def test_entity_creation():
    """Test basic entity creation and properties."""
    entity = Entity(
        id="test_entity",
        name="Test Entity",
        entity_type="individual",
        properties={"role": "activist"}
    )
    
    assert entity.id == "test_entity"
    assert entity.name == "Test Entity"
    assert entity.entity_type == "individual"
    assert entity.properties["role"] == "activist"
    assert all(rel_type in entity.relationships for rel_type in [
        "supports", "opposes", "controls", "influences", "threatens", "criticized_by"
    ])

def test_power_structure_relationships():
    """Test adding and retrieving relationships in power structure."""
    power = PowerStructure()
    
    # Add entities
    power.add_entity("entity1", "Entity One", "individual", {"role": "activist"})
    power.add_entity("entity2", "Entity Two", "organization", {"type": "corporation"})
    
    # Add relationship
    assert power.add_relationship("entity1", "entity2", "opposes")
    
    # Check relationship
    related = power.get_related_entities("entity1")
    assert len(related) == 1
    assert related[0].id == "entity2"

def test_contextual_analysis(detector):
    """Test contextual analysis of narrative involving known entities."""
    text = "Jimmy Kimmel criticizes RFK Jr's health advocacy stance"
    entities = ["kimmel", "rfk_jr"]
    
    analysis = detector.analyze_narrative_context(text, entities)
    
    assert len(analysis["entities_involved"]) == 2
    assert any(e["id"] == "kimmel" for e in analysis["entities_involved"])
    assert any(e["id"] == "rfk_jr" for e in analysis["entities_involved"])
    
    # Should identify relationships
    relationships = analysis["relationships_relevant"]
    assert len(relationships) > 0
    
    # Check for indirect relationship through media and pharma
    media_pharma = False
    for rel in relationships:
        if rel["source"] == "ABC Network" and "influenced_by" in rel["types"]:
            media_pharma = True
    assert media_pharma

def test_entity_temporal_context():
    """Test adding temporal context to entities."""
    entity = Entity(
        id="test_entity",
        name="Test Entity",
        entity_type="individual"
    )
    
    timestamp = datetime.now(UTC)
    entity.add_temporal_context("statement_made", timestamp)
    
    assert "statement_made" in entity.temporal_context
    assert entity.temporal_context["statement_made"] == timestamp

def test_invalid_entity_type():
    """Test handling of invalid entity type."""
    power = PowerStructure()
    entity = power.add_entity(
        "test",
        "Test Entity",
        "invalid_type"
    )
    assert entity is None

def test_relationship_retrieval_by_type(detector):
    """Test retrieving relationships of specific type."""
    related = detector.power_structure.get_related_entities(
        "rfk_jr",
        relationship_type="opposes"
    )
    
    assert len(related) == 1
    assert related[0].id == "big_pharma"