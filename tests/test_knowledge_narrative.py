import pytest
from datetime import datetime
from uuid import UUID

from gonzo.graph.state import GonzoState
from gonzo.nodes.knowledge_enhanced_narrative import KnowledgeEnhancedNarrative, enhance_narrative

@pytest.fixture
def sample_narrative_analysis():
    return {
        "raw_analysis": "The crypto-wolves are howling at the digital moon again...",
        "tweet_thread": [
            "🧵 1/3 The crypto-wolves are howling...",
            "🧵 2/3 Market manipulation in plain sight...",
            "🧵 3/3 History repeats, first as tragedy..."
        ],
        "timestamp": datetime.now().isoformat()
    }

@pytest.fixture
def mock_state(sample_narrative_analysis):
    state = GonzoState()
    state.save_to_memory(
        key="last_narrative_analysis",
        value=sample_narrative_analysis,
        permanent=True
    )
    return state

def test_extract_narrative_entities(mock_state, sample_narrative_analysis):
    enhancer = KnowledgeEnhancedNarrative()
    entities = enhancer._extract_narrative_entities(sample_narrative_analysis)
    
    assert len(entities) > 0
    assert entities[0].type == "narrative_event"
    assert isinstance(entities[0].id, UUID)
    assert sample_narrative_analysis["raw_analysis"] in entities[0].properties["content"].value

@pytest.mark.asyncio
async def test_enhance_narrative_flow(mock_state):
    result = await enhance_narrative(mock_state)
    
    assert result["next"] is not None
    
    # Verify memory updates
    narrative_analyses = mock_state.get_from_memory("narrative_analyses", "long_term")
    assert narrative_analyses is not None
    assert len(narrative_analyses) > 0
    
    latest = narrative_analyses[-1]
    assert "entity_id" in latest
    assert isinstance(latest["entity_id"], UUID)

def test_narrative_relationships(mock_state):
    enhancer = KnowledgeEnhancedNarrative()
    
    # Create two narrative entities
    entities1 = enhancer._extract_narrative_entities({
        "raw_analysis": "First narrative",
        "timestamp": datetime.now().isoformat()
    })
    
    # Add to memory
    mock_state.save_to_memory(
        key="narrative_analyses",
        value=[{"entity_id": entities1[0].id}],
        permanent=True
    )
    
    # Create relationships for new entity
    entities2 = enhancer._extract_narrative_entities({
        "raw_analysis": "Second narrative",
        "timestamp": datetime.now().isoformat()
    })
    
    relationships = enhancer._create_narrative_relationships(entities2[0], mock_state)
    
    assert len(relationships) > 0
    assert relationships[0].source_id == entities1[0].id
    assert relationships[0].target_id == entities2[0].id
    assert relationships[0].type == "narrative_sequence"