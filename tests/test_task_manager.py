import pytest
from unittest.mock import Mock, patch
from gonzo.tasks.task_manager import TaskManager, TaskInput
from gonzo.config import ANALYSIS_CONFIG

# Sample test data
SAMPLE_ENTITY_RESPONSE = '''
{
    "entities": [
        {
            "text": "John Smith",
            "type": "PERSON",
            "properties": {
                "category": "influencer",
                "future_impact": "Key figure in 2025 cryptocurrency adoption",
                "manipulation_risk": 0.7
            },
            "confidence": 0.9,
            "timestamp": 120.5
        }
    ]
}
'''

SAMPLE_TOPIC_RESPONSE = '''
{
    "segments": [
        {
            "text": "Discussion about blockchain technology",
            "topic": "Cryptocurrency Adoption",
            "category": "technology",
            "start_time": 120.0,
            "end_time": 180.0,
            "confidence": 0.85,
            "properties": {
                "narrative_type": "persuasion",
                "future_relevance": "Critical turning point in digital currency debate",
                "manipulation_tactics": ["appeal_to_fear", "false_urgency"]
            }
        }
    ]
}
'''

def create_mock_agent(response):
    """Create a mock agent that returns a specific response."""
    mock_agent = Mock()
    mock_agent.run.return_value = response
    return mock_agent

def test_task_manager_initialization():
    """Test TaskManager initialization."""
    mock_agent = Mock()
    manager = TaskManager(mock_agent)
    assert manager.agent == mock_agent

def test_prepare_prompt():
    """Test prompt preparation."""
    manager = TaskManager(Mock())
    
    task_input = TaskInput(
        task="entity_extraction",
        text="Sample text",
        chunk_index=0,
        total_chunks=1,
        context="Test context"
    )
    
    prompt = manager.prepare_prompt(task_input)
    assert "Sample text" in prompt
    assert "Test context" in prompt
    assert "chunk 1 of 1" in prompt

def test_validate_entity_output():
    """Test entity output validation."""
    manager = TaskManager(Mock())
    
    # Test valid output
    result = manager.validate_output("entity_extraction", SAMPLE_ENTITY_RESPONSE)
    assert "entities" in result
    assert len(result["entities"]) == 1
    assert result["entities"][0]["confidence"] >= ANALYSIS_CONFIG["min_confidence"]
    
    # Test invalid output
    result = manager.validate_output("entity_extraction", "invalid json")
    assert "error" in result

def test_validate_topic_output():
    """Test topic segmentation output validation."""
    manager = TaskManager(Mock())
    
    # Test valid output
    result = manager.validate_output("topic_segmentation", SAMPLE_TOPIC_RESPONSE)
    assert "segments" in result
    assert len(result["segments"]) == 1
    assert result["segments"][0]["confidence"] >= ANALYSIS_CONFIG["min_confidence"]
    
    # Test invalid output
    result = manager.validate_output("topic_segmentation", "invalid json")
    assert "error" in result

def test_execute_entity_task():
    """Test complete entity extraction task execution."""
    mock_agent = create_mock_agent(SAMPLE_ENTITY_RESPONSE)
    manager = TaskManager(mock_agent)
    
    task_input = TaskInput(
        task="entity_extraction",
        text="Sample text about John Smith",
        chunk_index=0,
        total_chunks=1
    )
    
    result = manager.execute_task(task_input)
    assert "entities" in result
    assert len(result["entities"]) == 1
    assert result["entities"][0]["text"] == "John Smith"

def test_execute_topic_task():
    """Test complete topic segmentation task execution."""
    mock_agent = create_mock_agent(SAMPLE_TOPIC_RESPONSE)
    manager = TaskManager(mock_agent)
    
    task_input = TaskInput(
        task="topic_segmentation",
        text="Discussion about blockchain technology",
        chunk_index=0,
        total_chunks=1
    )
    
    result = manager.execute_task(task_input)
    assert "segments" in result
    assert len(result["segments"]) == 1
    assert result["segments"][0]["topic"] == "Cryptocurrency Adoption"

def test_confidence_filtering():
    """Test filtering of low confidence results."""
    low_confidence_response = '''
    {
        "entities": [
            {
                "text": "Low confidence entity",
                "type": "CONCEPT",
                "confidence": 0.3
            }
        ]
    }
    '''
    
    manager = TaskManager(create_mock_agent(low_confidence_response))
    result = manager.validate_output("entity_extraction", low_confidence_response)
    assert len(result["entities"]) == 0

def test_topic_limit_per_chunk():
    """Test limiting number of topics per chunk."""
    many_topics_response = {
        "segments": [
            {"topic": f"Topic {i}", "confidence": 0.9}
            for i in range(10)
        ]
    }
    
    manager = TaskManager(Mock())
    result = manager.validate_output(
        "topic_segmentation", 
        str(many_topics_response)
    )
    
    assert len(result["segments"]) <= ANALYSIS_CONFIG["max_topics_per_chunk"]
