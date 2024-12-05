from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel
import aiohttp
from aiohttp import TCPConnector
import ssl

class CryptoPrice(BaseModel):
    symbol: str
    price: float
    last_update: datetime
    volume_24h: Optional[float] = None
    change_24h: Optional[float] = None

class CryptoAPIClient:
    """Client for CryptoCompare API"""
    
    def __init__(self, api_key: Optional[str] = None, verify_ssl: bool = True):
        self.base_url = "https://min-api.cryptocompare.com/data"
        self.api_key = api_key
        self.session: Optional[aiohttp.ClientSession] = None
        self.verify_ssl = verify_ssl
    
    async def _ensure_session(self):
        if self.session is None:
            # Create SSL context if needed
            if not self.verify_ssl:
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
                connector = TCPConnector(ssl=ssl_context)
            else:
                connector = None
            
            # Create session with proper headers and connector
            self.session = aiohttp.ClientSession(connector=connector)
            if self.api_key:
                self.session.headers.update({"authorization": f"Apikey {self.api_key}"})
    
    async def get_price(self, symbol: str, currency: str = "USD") -> CryptoPrice:
        """Get current price for a cryptocurrency"""
        await self._ensure_session()
        
        url = f"{self.base_url}/price"
        params = {
            "fsym": symbol.upper(),
            "tsyms": currency.upper(),
            "extraParams": "GonzoAgent"
        }
        
        async with self.session.get(url, params=params) as response:
            if response.status != 200:
                raise Exception(f"API request failed: {await response.text()}")
            
            data = await response.json()
            return CryptoPrice(
                symbol=symbol,
                price=data[currency],
                last_update=datetime.now(),
            )
    
    async def get_multiple_prices(self, symbols: List[str], currency: str = "USD") -> Dict[str, CryptoPrice]:
        """Get current prices for multiple cryptocurrencies"""
        await self._ensure_session()
        
        url = f"{self.base_url}/pricemulti"
        params = {
            "fsyms": ",".join(s.upper() for s in symbols),
            "tsyms": currency.upper(),
            "extraParams": "GonzoAgent"
        }
        
        async with self.session.get(url, params=params) as response:
            if response.status != 200:
                raise Exception(f"API request failed: {await response.text()}")
            
            data = await response.json()
            return {
                symbol: CryptoPrice(
                    symbol=symbol,
                    price=price_data[currency],
                    last_update=datetime.now()
                )
                for symbol, price_data in data.items()
            }
    
    async def close(self):
        """Close the API client session"""
        if self.session:
            await self.session.close()
            self.session = None