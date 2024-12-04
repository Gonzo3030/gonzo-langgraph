import pytest
from datetime import datetime
from ..gonzo.nodes.crypto import create_thread, analyze_crypto
from ..gonzo.types import GonzoState, Message

def test_create_thread():
    """Test breaking long crypto analysis into tweet-sized chunks."""
    test_text = "This is a test of the crypto analysis system. It should be broken into multiple tweets. Each tweet should be properly formatted with the crypto emoji."
    thread = create_thread(test_text)
    
    assert all(tweet.startswith('💰') for tweet in thread)
    assert all(len(tweet) <= 280 for tweet in thread)
    assert all(f"{i+1}/{len(thread)}" in tweet for i, tweet in enumerate(thread))

def test_crypto_analysis_basic():
    """Test basic crypto market analysis functionality."""
    # Setup test state
    test_state = GonzoState(
        messages=[Message(role="user", content="What's your take on Bitcoin's latest price action?")],
        context={},
        steps=[],
        response=""
    )
    
    # Run analysis
    result = analyze_crypto(test_state)
    
    # Verify structure
    assert "crypto_analysis" in result["context"]
    assert "structured_report" in result["context"]
    assert "tweet_thread" in result["context"]
    assert "analysis_timestamp" in result["context"]
    
    # Verify steps
    assert len(result["steps"]) == 1
    assert result["steps"][0]["node"] == "crypto_analysis"
    
    # Print analysis for review
    print("Raw Crypto Analysis:")
    print(result["context"]["crypto_analysis"])
    print("\nStructured Report:")
    for section, content in result["context"]["structured_report"].items():
        print(f"\n{section}:")
        print(content)
    print("\nTweet Thread:")
    for tweet in result["context"]["tweet_thread"]:
        print(f"\n{tweet}")
    
    # Print full response
    print("\nGonzo Crypto Analysis:")
    print("=" * 50)
    print(result["response"])
    print("=" * 50)

def test_crypto_analysis_market_crash():
    """Test analysis during market crash scenarios."""
    test_state = GonzoState(
        messages=[Message(role="user", content="The crypto market just crashed 40% in 24 hours! What's really going on?")],
        context={},
        steps=[],
        response=""
    )
    
    result = analyze_crypto(test_state)
    print("Market Crash Analysis:")
    print("=" * 50)
    print(result["response"])
    print("=" * 50)

def test_crypto_analysis_error_handling():
    """Test error handling with empty state."""
    test_state = GonzoState(
        messages=[],
        context={},
        steps=[],
        response=""
    )
    
    result = analyze_crypto(test_state)
    print(f"Crypto analysis error: {result['context'].get('crypto_error')}")
    
    assert "crypto_error" in result["context"]
    assert result["steps"][0]["node"] == "crypto_analysis"
    assert "error" in result["steps"][0]