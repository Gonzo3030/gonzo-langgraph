import pytest
from datetime import datetime
from gonzo.causality.types import CausalEvent, EventCategory, EventScope
from gonzo.causality.semantic_matcher import SemanticMatcher, PatternMatcher

@pytest.fixture
def historical_events():
    """Sample historical events for testing."""
    return [
        CausalEvent(
            id="early-crypto-regulation",
            timestamp=datetime(2023, 6, 15),
            description="SEC begins aggressive enforcement against major crypto exchanges",
            category=EventCategory.CRYPTO,
            scope=EventScope.NATIONAL,
            metadata={
                "location": "United States",
                "entities": ["SEC", "Binance", "Coinbase"]
            }
        ),
        CausalEvent(
            id="tech-consolidation",
            timestamp=datetime(2023, 9, 1),
            description="Major tech companies consolidate AI research under government oversight",
            category=EventCategory.TECH,
            scope=EventScope.GLOBAL,
            metadata={
                "entities": ["OpenAI", "DeepMind", "Anthropic"],
                "technology": "artificial intelligence"
            }
        ),
        CausalEvent(
            id="social-uprising",
            timestamp=datetime(2023, 11, 30),
            description="Widespread protests against digital identity systems",
            category=EventCategory.SOCIAL,
            scope=EventScope.GLOBAL,
            metadata={
                "trigger": "privacy concerns",
                "outcome": "policy reversal"
            }
        )
    ]

@pytest.mark.asyncio
async def test_basic_similarity_matching(historical_events):
    matcher = SemanticMatcher()
    
    # Test crypto regulation matching
    matches = await matcher.find_semantic_matches(
        current_event="New cryptocurrency exchange regulations proposed by EU",
        current_category=EventCategory.CRYPTO,
        current_scope=EventScope.REGIONAL,
        historical_events=historical_events
    )
    
    assert len(matches) > 0
    assert any(m.event.id == "early-crypto-regulation" for m in matches)
    assert all(0 <= m.similarity_score <= 1 for m in matches)

@pytest.mark.asyncio
async def test_cross_category_pattern_matching(historical_events):
    matcher = PatternMatcher()
    
    # Test finding control patterns across categories
    patterns = await matcher.find_matching_patterns(
        current_event="Government announces AI model registration requirements",
        category=EventCategory.TECH,
        scope=EventScope.NATIONAL,
        historical_events=historical_events
    )
    
    assert len(patterns) > 0
    # Should find regulatory pattern similarities with crypto
    assert any(
        "regulation" in pattern.lower() 
        for pattern in patterns.keys()
    )

@pytest.mark.asyncio
async def test_future_implications(historical_events):
    # Add a future event
    future_event = CausalEvent(
        id="crypto-schism",
        timestamp=datetime(2027, 3, 15),
        description="The Great Crypto Schism: Mass exodus from regulated exchanges",
        category=EventCategory.CRYPTO,
        scope=EventScope.GLOBAL,
        metadata={
            "trigger": "privacy elimination",
            "outcome": "parallel systems"
        }
    )
    
    all_events = historical_events + [future_event]
    matcher = PatternMatcher()
    
    patterns = await matcher.find_matching_patterns(
        current_event="Major exchange implements mandatory identity verification",
        category=EventCategory.CRYPTO,
        scope=EventScope.GLOBAL,
        historical_events=all_events
    )
    
    # Should identify pattern leading to the schism
    assert any(
        future_event in events
        for events in patterns.values()
    )

@pytest.mark.asyncio
async def test_different_scopes(historical_events):
    matcher = SemanticMatcher()
    
    # Test how scope affects matching
    local_matches = await matcher.find_semantic_matches(
        current_event="Local cryptocurrency exchange implements new KYC rules",
        current_category=EventCategory.CRYPTO,
        current_scope=EventScope.LOCAL,
        historical_events=historical_events,
        threshold=0.5  # Lower threshold to catch scope differences
    )
    
    global_matches = await matcher.find_semantic_matches(
        current_event="Global cryptocurrency exchange implements new KYC rules",
        current_category=EventCategory.CRYPTO,
        current_scope=EventScope.GLOBAL,
        historical_events=historical_events,
        threshold=0.5
    )
    
    # Global events should have higher similarity scores
    assert max(m.similarity_score for m in global_matches) > \
           max(m.similarity_score for m in local_matches)
