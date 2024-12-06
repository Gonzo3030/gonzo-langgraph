import pytest
from datetime import datetime
from gonzo.persistence import GonzoCheckpointer
from gonzo.persistence.store import InMemoryStore

@pytest.fixture
def store():
    """Create test store."""
    return InMemoryStore()

@pytest.fixture
def checkpointer(store):
    """Create test checkpointer."""
    return GonzoCheckpointer(store, "test_thread")

@pytest.mark.asyncio
async def test_basic_persistence(checkpointer):
    """Test basic state persistence and restoration."""
    # Create test state
    test_state = {
        "messages": ["test"],
        "category": "test",
        "timestamp": datetime.now().isoformat()
    }
    
    # Persist state
    await checkpointer.persist(test_state, step=1)
    
    # Restore state
    restored = await checkpointer.restore(step=1)
    assert restored == test_state

@pytest.mark.asyncio
async def test_multiple_checkpoints(checkpointer):
    """Test handling multiple checkpoints."""
    # Create and persist multiple states
    states = [
        {"step": i, "data": f"test_{i}"}
        for i in range(3)
    ]
    
    for i, state in enumerate(states):
        await checkpointer.persist(state, step=i)
    
    # Check checkpoint listing
    checkpoints = await checkpointer.list_checkpoints()
    assert len(checkpoints) == 3
    
    # Verify order
    assert checkpoints == [
        f"checkpoint_test_thread_{i}"
        for i in range(3)
    ]

@pytest.mark.asyncio
async def test_checkpoint_deletion(checkpointer):
    """Test checkpoint deletion."""
    # Create test state
    test_state = {"data": "test"}
    
    # Persist and then delete
    await checkpointer.persist(test_state, step=1)
    await checkpointer.delete(step=1)
    
    # Verify deletion
    restored = await checkpointer.restore(step=1)
    assert restored is None

@pytest.mark.asyncio
async def test_checkpoint_clear(checkpointer):
    """Test clearing all checkpoints."""
    # Create multiple checkpoints
    for i in range(3):
        await checkpointer.persist({"step": i}, step=i)
    
    # Clear all
    await checkpointer.clear()
    
    # Verify all cleared
    checkpoints = await checkpointer.list_checkpoints()
    assert len(checkpoints) == 0