import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from gonzo.integrations.crypto_api import CryptoAPIClient, CryptoPrice

@pytest.fixture
def mock_session():
    with patch('aiohttp.ClientSession') as mock:
        yield mock

@pytest.mark.asyncio
async def test_get_price(mock_session):
    # Mock response
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.json.return_value = {"USD": 50000.0}
    
    # Setup session
    session_instance = MagicMock()
    session_instance.get.return_value.__aenter__.return_value = mock_response
    mock_session.return_value = session_instance
    
    client = CryptoAPIClient()
    price = await client.get_price("BTC")
    
    assert isinstance(price, CryptoPrice)
    assert price.symbol == "BTC"
    assert price.price == 50000.0
    assert isinstance(price.last_update, datetime)

@pytest.mark.asyncio
async def test_get_multiple_prices(mock_session):
    # Mock response
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.json.return_value = {
        "BTC": {"USD": 50000.0},
        "ETH": {"USD": 3000.0}
    }
    
    # Setup session
    session_instance = MagicMock()
    session_instance.get.return_value.__aenter__.return_value = mock_response
    mock_session.return_value = session_instance
    
    client = CryptoAPIClient()
    prices = await client.get_multiple_prices(["BTC", "ETH"])
    
    assert len(prices) == 2
    assert isinstance(prices["BTC"], CryptoPrice)
    assert isinstance(prices["ETH"], CryptoPrice)
    assert prices["BTC"].price == 50000.0
    assert prices["ETH"].price == 3000.0

@pytest.mark.asyncio
async def test_api_error_handling(mock_session):
    # Mock error response
    mock_response = MagicMock()
    mock_response.status = 400
    mock_response.text.return_value = "Bad Request"
    
    # Setup session
    session_instance = MagicMock()
    session_instance.get.return_value.__aenter__.return_value = mock_response
    mock_session.return_value = session_instance
    
    client = CryptoAPIClient()
    with pytest.raises(Exception, match="API request failed"):
        await client.get_price("BTC")