import pytest
from datetime import datetime, timedelta
from gonzo.memory.store import MemoryStore

@pytest.fixture
def memory_store():
    """Create a fresh memory store for each test."""
    return MemoryStore()

@pytest.fixture
def sample_data():
    """Create sample data for testing."""
    return {
        "present_event": {
            "type": "market_event",
            "description": "Major crypto adoption by institutional investors",
            "timestamp": datetime.now().isoformat()
        },
        "future_event": {
            "type": "consequence",
            "description": "Decentralized finance becomes dominant economic model",
            "timestamp": datetime(3030, 1, 1).isoformat()
        },
        "past_event": {
            "type": "historical",
            "description": "Early warnings about media manipulation",
            "timestamp": datetime(1974, 1, 1).isoformat()
        }
    }

@pytest.mark.asyncio
async def test_basic_store_operations(memory_store):
    """Test basic store operations (set, get, delete, exists)."""
    # Set and get
    await memory_store.set("test_key", "test_value")
    value = await memory_store.get("test_key")
    assert value == "test_value"
    
    # Exists
    exists = await memory_store.exists("test_key")
    assert exists is True
    
    # Delete
    await memory_store.delete("test_key")
    value = await memory_store.get("test_key")
    assert value is None

@pytest.mark.asyncio
async def test_timeline_storage(memory_store, sample_data):
    """Test timeline-specific storage and retrieval."""
    # Store events in different timelines
    await memory_store.set(
        "present_key",
        sample_data["present_event"],
        timeline="present"
    )
    await memory_store.set(
        "future_key",
        sample_data["future_event"],
        timeline="3030"
    )
    await memory_store.set(
        "past_key",
        sample_data["past_event"],
        timeline="1970s"
    )
    
    # Get timeline-specific entries
    present_entries = await memory_store.get_timeline_entries(timeline="present")
    assert len(present_entries) == 1
    assert present_entries[0]["type"] == "market_event"
    
    future_entries = await memory_store.get_timeline_entries(timeline="3030")
    assert len(future_entries) == 1
    assert future_entries[0]["type"] == "consequence"

@pytest.mark.asyncio
async def test_pattern_recognition(memory_store, sample_data):
    """Test pattern recognition capabilities."""
    # Store related events
    await memory_store.set(
        "present_key",
        sample_data["present_event"],
        timeline="present"
    )
    await memory_store.set(
        "future_key",
        sample_data["future_event"],
        timeline="3030"
    )
    
    # Find patterns
    patterns = await memory_store.find_patterns("timeline_correlation")
    assert len(patterns) > 0
    assert "present_event" in patterns[0]
    assert "future_event" in patterns[0]
    assert "confidence" in patterns[0]

@pytest.mark.asyncio
async def test_metadata_tracking(memory_store):
    """Test metadata tracking functionality."""
    # Initial metadata
    assert "created_at" in memory_store.metadata
    assert "total_entries" in memory_store.metadata
    assert memory_store.metadata["total_entries"] == 0
    
    # Add entries and check metadata updates
    await memory_store.set("key1", "value1")
    assert memory_store.metadata["total_entries"] == 1
    
    await memory_store.set("key2", "value2")
    assert memory_store.metadata["total_entries"] == 2
    
    # Check last_updated is being maintained
    original_update = memory_store.metadata["last_updated"]
    await memory_store.set("key3", "value3")
    new_update = memory_store.metadata["last_updated"]
    assert new_update > original_update

@pytest.mark.asyncio
async def test_time_based_queries(memory_store):
    """Test time-based entry queries."""
    now = datetime.now()
    
    # Add entries at different times
    await memory_store.set("past", {"time": "past"}, timeline="present")
    await memory_store.set("present", {"time": "present"}, timeline="present")
    await memory_store.set("future", {"time": "future"}, timeline="present")
    
    # Query with time window
    entries = await memory_store.get_timeline_entries(
        start_time=now - timedelta(hours=1),
        end_time=now + timedelta(hours=1),
        timeline="present"
    )
    
    assert len(entries) > 0