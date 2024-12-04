import pytest
from typing import Dict, Any
from langchain_core.messages import HumanMessage
from gonzo.nodes.crypto import analyze_crypto, create_thread
from gonzo.types import GonzoState, create_initial_state

def test_create_thread():
    # Test thread creation with sample crypto analysis
    text = "First insight about Bitcoin markets. Second point about institutional adoption. Third very detailed analysis about the technical indicators and market sentiment that should definitely be split into multiple tweets."
    thread = create_thread(text, max_length=100)
    
    assert len(thread) > 1  # Should create multiple tweets
    assert all(len(tweet) <= 100 for tweet in thread)  # Each tweet within limit
    assert all('💰' in tweet for tweet in thread)  # Crypto emoji in each
    assert all("/" in tweet for tweet in thread)  # Thread numbering

def test_crypto_analysis_basic():
    # Arrange
    initial_state = create_initial_state(
        HumanMessage(content="Bitcoin just broke $50k and everyone's calling for $100k. "  
                    "What's really driving this rally?")
    )
    
    # Act
    updates = analyze_crypto(initial_state)
    
    # Print analysis for inspection
    print("\nGonzo Crypto Analysis (Basic):\n" + "=" * 50)
    print(updates["response"])
    print("=" * 50 + "\n")
    
    # Assert
    assert "crypto_analysis" in updates["context"]
    assert "structured_report" in updates["context"]
    assert "tweet_thread" in updates["context"]
    assert len(updates["context"]["tweet_thread"]) > 0
    assert len(updates["context"]["crypto_analysis"]) > 100
    assert updates["steps"][0]["node"] == "crypto_analysis"
    assert "tweet_thread" in updates["steps"][0]
    assert updates["response"].startswith('💰')  # Crypto emoji

def test_crypto_analysis_market_crash():
    # Arrange
    initial_state = create_initial_state(
        HumanMessage(content="The crypto market just crashed 40% in 24 hours! " 
                    "What's really going on behind the scenes?")
    )
    
    # Act
    updates = analyze_crypto(initial_state)
    
    # Print analysis for inspection
    print("\nGonzo Analysis (Market Crash):\n" + "=" * 50)
    print(updates["response"])
    print("=" * 50 + "\n")
    
    analysis = updates["context"]["crypto_analysis"]
    report = updates["context"]["structured_report"]
    thread = updates["context"]["tweet_thread"]
    
    # Assert - Check for Gonzo style markers and crash analysis
    analysis_lower = analysis.lower()
    # Should contain market crash terminology
    assert any(term in analysis_lower for term in ["crash", "liquidation", "panic", "whale", "manipulation"])
    # Should be substantial
    assert len(analysis) > 200
    # Should have structured sections
    assert len(report) >= 3  # At least 3 sections
    # Should maintain Gonzo voice
    gonzo_markers = ["!", "*", "-", "..."]
    assert any(term in analysis for term in gonzo_markers)
    # Check thread
    assert len(thread) > 0
    assert all(len(t) <= 280 for t in thread)  # Twitter limit

def test_crypto_analysis_error_handling():
    # Arrange - create invalid state
    invalid_state = create_initial_state("")
    invalid_state["messages"] = []
    
    # Act
    updates = analyze_crypto(invalid_state)
    
    # Assert
    assert "crypto_error" in updates["context"]
    assert len(updates["steps"]) == 1
    assert "error" in updates["steps"][0]
    assert "neural networks" in updates["response"].lower()  # Check for crypto-themed error message