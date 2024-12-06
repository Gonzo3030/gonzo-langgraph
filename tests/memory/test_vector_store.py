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
