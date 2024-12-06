import pytest
from datetime import datetime, timedelta
from gonzo.memory.store import VectorMemoryStore
from .mock_embeddings import MockEmbeddings

@pytest.fixture
def vector_store():
    """Create a fresh vector store for each test."""
    return VectorMemoryStore(embeddings=MockEmbeddings())

@pytest.fixture
def sample_entries():
    """Create sample entries for testing."""
    return {
        "crypto_adoption": {
            "type": "market_event",
            "description": "Major institutional adoption of cryptocurrency",
            "impact": "High institutional investment flowing into crypto markets",
            "timestamp": datetime.now().isoformat()
        },
        "defi_dominance": {
            "type": "future_event",
            "description": "DeFi becomes dominant financial system",
            "impact": "Traditional banking system largely replaced by DeFi",
            "timestamp": datetime(3030, 1, 1).isoformat()
        }
    }

@pytest.mark.asyncio
async def test_basic_vector_operations(vector_store):
    """Test basic vector store operations."""
    # Test store and retrieve
    entry = {"description": "Test entry", "type": "test"}
    await vector_store.set("test_key", entry)
    
    retrieved = await vector_store.get("test_key")
    assert retrieved == entry
    
    # Test deletion
    await vector_store.delete("test_key")
    assert await vector_store.get("test_key") is None

@pytest.mark.asyncio
async def test_semantic_search(vector_store, sample_entries):
    """Test semantic search capabilities."""
    # Store sample entries
    for key, entry in sample_entries.items():
        await vector_store.set(key, entry)
    
    # Search for crypto-related content
    results = await vector_store.semantic_search(
        "cryptocurrency financial system",
        n_results=2
    )
    
    assert len(results) == 2
    assert all(isinstance(score, float) for _, score in results)
    assert all(0 <= score <= 1 for _, score in results)

@pytest.mark.asyncio
async def test_timeline_correlation(vector_store, sample_entries):
    """Test timeline correlation detection."""
    # Store entries in different timelines
    await vector_store.set(
        "crypto_now",
        sample_entries["crypto_adoption"],
        timeline="present"
    )
    await vector_store.set(
        "defi_future",
        sample_entries["defi_dominance"],
        timeline="3030"
    )
    
    # Find correlations
    patterns = await vector_store.find_patterns("timeline_correlation")
    
    assert len(patterns) > 0
    assert "confidence" in patterns[0]
    assert patterns[0]["confidence"] > 0.5  # Should have meaningful confidence