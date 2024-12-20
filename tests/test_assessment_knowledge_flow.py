import pytest
import asyncio
from datetime import datetime, timedelta

from gonzo.graph.state import GonzoState
from gonzo.nodes.knowledge_enhanced_assessment import enhance_assessment
from gonzo.types import Message

@pytest.mark.asyncio
async def test_assessment_knowledge_flow():
    # Create initial state with a crypto-related message
    state = GonzoState()
    state.state['messages'] = [
        Message(
            content="""
            Bitcoin just hit a new all-time high amidst massive institutional buying.
            The market sentiment has completely flipped from last month's bearish trend.
            Major banks are now announcing crypto custody services.
            """,
            timestamp=datetime.now()
        )
    ]
    
    # Run enhanced assessment
    result1 = await enhance_assessment(state)
    assert result1['next'] == 'crypto'
    
    # Verify knowledge graph integration
    topic_assessments = state.get_from_memory("topic_assessments", "long_term")
    assert topic_assessments is not None
    assert len(topic_assessments) == 1
    assert 'entity_id' in topic_assessments[0]
    
    # Add a related narrative message
    state.state['messages'] = [
        Message(
            content="""
            The mainstream media's sudden shift to positive crypto coverage is suspicious.
            The same outlets that were spreading FUD last month are now pumping Bitcoin.
            This looks like coordinated narrative manipulation.
            """,
            timestamp=datetime.now() + timedelta(hours=2)
        )
    ]
    
    # Run second assessment
    result2 = await enhance_assessment(state)
    print(f"\nSecond assessment result: {result2}")
    assert result2['next'] == 'narrative'
    
    # Verify topic relationships
    topic_assessments = state.get_from_memory("topic_assessments", "long_term")
    print(f"\nTopic assessments after second message: {topic_assessments}")
    assert len(topic_assessments) == 2
    
    latest = topic_assessments[-1]
    print(f"\nLatest assessment: {latest}")
    assert 'relationships' in latest
    assert len(latest['relationships']) > 0
    
    # Add a general message
    state.state['messages'] = [
        Message(
            content="""
            The weather has been unusually warm lately.
            Climate patterns are showing concerning trends.
            """,
            timestamp=datetime.now() + timedelta(hours=4)
        )
    ]
    
    # Run third assessment
    result3 = await enhance_assessment(state)
    assert result3['next'] == 'general'
    
    # Print analysis for manual verification
    print("\nAssessment Flow:")
    for i, assessment in enumerate(topic_assessments, 1):
        print(f"\nAssessment {i}:")
        print(f"Category: {assessment['category']}")
        print(f"Content: {assessment['message_content'][:100]}...")
        print(f"Relationships: {len(assessment.get('relationships', []))}")
        if 'relationships' in assessment:
            print(f"Relationship IDs: {assessment['relationships']}")
    
    return state