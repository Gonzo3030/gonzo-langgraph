import pytest
from unittest.mock import AsyncMock
from datetime import datetime
from langchain.schema import HumanMessage
from gonzo.nodes.new_crypto import analyze_crypto, analysis_chain
from gonzo.graph.state import GonzoState

# Test data
SAMPLE_ANALYSIS = """🏦 MARKET ANALYSIS
Bullish momentum with strong volume.

📊 TECHNICAL INDICATORS
All indicators point up.

🌊 SOCIAL SENTIMENT
Very positive community feedback.

⚖️ REGULATORY LANDSCAPE
Regulators seem supportive.

🔮 FUTURE IMPLICATIONS
Long-term outlook positive."""

@pytest.fixture
def state():
    return GonzoState()

@pytest.fixture
def mock_chain():
    mock = AsyncMock()
    mock.ainvoke.return_value = {"output": SAMPLE_ANALYSIS}
    return mock