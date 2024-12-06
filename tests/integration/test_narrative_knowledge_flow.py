import pytest
import asyncio
from datetime import datetime, timedelta

from gonzo.graph.state import GonzoState
from gonzo.nodes.new_narrative import analyze_narrative
from gonzo.nodes.knowledge_enhanced_narrative import enhance_narrative

@pytest.mark.asyncio
async def test_full_narrative_flow():
    # Create initial state with a test message
    state = GonzoState()
    state.state['messages'] = [
        type('Message', (), {
            'content': """
            The crypto markets are showing classic signs of manipulation again. 
            Bitcoin's sudden pump coincides perfectly with the SEC's latest FUD campaign. 
            Meanwhile, the mainstream media narrative shifts like a weathervane in a tornado - 
            first it's 'crypto is dead', then suddenly it's 'institutional adoption is here'. 
            The same old players are pulling the same old strings, just with fancier algorithms 
            and slicker PR campaigns. You can smell the sulfur of market manipulation from a mile away.
            """,
            'timestamp': datetime.now()
        })()
    ]
    
    # Run narrative analysis
    narrative_result = await analyze_narrative(state)
    assert narrative_result['next'] == 'respond'
    assert 'response' in narrative_result
    
    # Run knowledge enhancement
    knowledge_result = await enhance_narrative(state)
    assert knowledge_result['next'] is not None
    
    # Verify memory updates
    narrative_analyses = state.get_from_memory("narrative_analyses", "long_term")
    assert narrative_analyses is not None
    assert len(narrative_analyses) > 0
    
    latest = narrative_analyses[-1]
    assert 'entity_id' in latest
    assert 'relationships' in latest
    
    # Add another related narrative after some time
    state.state['messages'] = [
        type('Message', (), {
            'content': """
            The aftermath of yesterday's crypto pump is exactly what you'd expect 
            in this rigged casino. The same institutional players who were spreading 
            FUD last week are now touting their 'strategic blockchain investments'. 
            The pattern is so obvious it hurts - create fear, accumulate in the dark, 
            pump in the light. The more things change, the more they stay the same in 
            this digital Wild West.
            """,
            'timestamp': datetime.now() + timedelta(days=1)
        })()
    ]
    
    # Run second analysis
    narrative_result2 = await analyze_narrative(state)
    knowledge_result2 = await enhance_narrative(state)
    
    # Verify temporal relationships
    narrative_analyses = state.get_from_memory("narrative_analyses", "long_term")
    assert len(narrative_analyses) == 2
    
    # Print analysis for manual verification
    print("\nFirst Analysis:")
    print(narrative_analyses[0]['raw_analysis'][:200] + '...')
    print("\nSecond Analysis:")
    print(narrative_analyses[1]['raw_analysis'][:200] + '...')
    
    return state  # Return state for further inspection if needed

if __name__ == '__main__':
    # Run the test and capture the state
    state = asyncio.run(test_full_narrative_flow())
    
    # Print additional debug info
    print("\nMemory Contents:")
    for key in ['last_narrative_analysis', 'narrative_analyses']:
        value = state.get_from_memory(key, "long_term")
        if value:
            print(f"\n{key}:")
            print(f"- Type: {type(value)}")
            print(f"- Length/Size: {len(value) if isinstance(value, (list, dict)) else 'N/A'}")
