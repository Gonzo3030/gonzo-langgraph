import pytest
import os
from dotenv import load_dotenv
from gonzo.integrations.crypto_api import CryptoAPIClient

# Load environment variables
load_dotenv()

@pytest.fixture
def api_client():
    api_key = os.getenv('CRYPTOCOMPARE_API_KEY')
    # Use verify_ssl=False for development/testing
    return CryptoAPIClient(api_key=api_key, verify_ssl=False)

@pytest.mark.asyncio
async def test_live_price_fetch(api_client):
    """Test actual API call to CryptoCompare"""
    try:
        # Get Bitcoin price
        btc_price = await api_client.get_price('BTC')
        assert btc_price.symbol == 'BTC'
        assert btc_price.price > 0
        print(f'\nCurrent BTC price: ${btc_price.price:,.2f}')
        
        # Test multiple prices
        prices = await api_client.get_multiple_prices(['BTC', 'ETH', 'DOGE'])
        assert len(prices) == 3
        assert all(price.price > 0 for price in prices.values())
        
        # Print all prices for verification
        for symbol, price_data in prices.items():
            print(f'{symbol} price: ${price_data.price:,.2f}')
            
    finally:
        # Always close the client session
        await api_client.close()