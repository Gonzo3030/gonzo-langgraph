import pytest
from datetime import datetime, timedelta
from typing import Dict, Any
from gonzo.causality.checkpointing import CausalAnalysisCheckpointer, AnalysisCache
from gonzo.causality.types import CausalEvent, TimelineChain, EventCategory, EventScope

@pytest.fixture
def checkpointer():
    return CausalAnalysisCheckpointer(ttl=10)  # 10 second TTL for testing

@pytest.fixture
def sample_state() -> Dict[str, Any]:
    event = CausalEvent(
        id="test-event",
        timestamp=datetime.now(),
        description="Test event",
        category=EventCategory.CRYPTO,
        scope=EventScope.GLOBAL
    )
    
    chain = TimelineChain(
        id="test-chain",
        name="Test Chain",
        description="Test timeline chain",
        events=[event],
        final_outcome="Test outcome",
        prevention_points=[datetime.now()],
        warning_signs=["Warning 1"]
    )
    
    return {
        'events': {'test-event': event},
        'chains': {'test-chain': chain},
        'metadata': {'test': True}
    }

@pytest.mark.asyncio
async def test_persist_and_load(checkpointer, sample_state):
    key = "test_key"
    await checkpointer.persist(key, sample_state)
    loaded = await checkpointer.load(key)
    assert loaded is not None
    assert loaded['events']['test-event'].id == "test-event"
    assert loaded['chains']['test-chain'].name == "Test Chain"

@pytest.mark.asyncio
async def test_expiration(checkpointer, sample_state):
    key = "test_key"
    await checkpointer.persist(key, sample_state)
    # Wait for TTL
    await asyncio.sleep(11)
    loaded = await checkpointer.load(key)
    assert loaded is None

@pytest.mark.asyncio
async def test_clear_expired(checkpointer, sample_state):
    # Add some entries
    await checkpointer.persist("fresh", sample_state)
    await asyncio.sleep(11)
    await checkpointer.persist("stale", sample_state)
    
    # Clear expired
    await checkpointer.clear_expired()
    
    stats = checkpointer.get_cache_stats()
    assert stats['total_entries'] == 1
    assert stats['expired_entries'] == 0

@pytest.mark.asyncio
async def test_key_generation(checkpointer):
    key = checkpointer.generate_key("test", 123, EventCategory.CRYPTO)
    assert isinstance(key, str)
    assert "test" in key
    assert "123" in key
    assert "CRYPTO" in key
