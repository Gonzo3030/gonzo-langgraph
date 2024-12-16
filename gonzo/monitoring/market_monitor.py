"""Cryptocurrency market monitoring implementation."""
import os
from typing import Dict, Any, List
from datetime import datetime, timedelta
import aiohttp

from .real_time_monitor import MarketEvent

class CryptoMarketMonitor:
    """Monitors cryptocurrency markets using CryptoCompare API."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://min-api.cryptocompare.com/data"
        self.watched_pairs = [
            "BTC/USD", "ETH/USD", "BNB/USD",
            "XRP/USD", "SOL/USD", "DOGE/USD"
        ]
        self.historical_data: Dict[str, List[Dict[str, float]]] = {}
    
    async def fetch_market_data(self, symbol: str) -> Dict[str, Any]:
        """Fetch current market data for a symbol."""
        url = f"{self.base_url}/v2/histominute"
        params = {
            "fsym": symbol.split("/")[0],
            "tsym": "USD",
            "limit": 60  # Last hour
        }
        headers = {"authorization": f"Bearer {self.api_key}"}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers) as response:
                data = await response.json()
                return data.get("Data", {})
    
    def detect_anomalies(self, current: float, historical: List[float]) -> Dict[str, float]:
        """Detect price and volume anomalies."""
        if not historical:
            return {}
            
        avg = sum(historical) / len(historical)
        std = (sum((x - avg) ** 2 for x in historical) / len(historical)) ** 0.5
        
        z_score = (current - avg) / std if std > 0 else 0
        
        return {
            "z_score": z_score,
            "deviation_percent": ((current - avg) / avg) * 100
        }
    
    def calculate_indicators(self, data: List[Dict[str, float]]) -> Dict[str, float]:
        """Calculate technical indicators from price data."""
        if not data:
            return {}
            
        prices = [d.get("close", 0) for d in data]
        volumes = [d.get("volume", 0) for d in data]
        
        # Basic indicators
        price_change = (prices[-1] - prices[0]) / prices[0] * 100
        volume_change = (volumes[-1] - volumes[0]) / volumes[0] * 100
        
        # Detect anomalies
        price_anomalies = self.detect_anomalies(prices[-1], prices)
        volume_anomalies = self.detect_anomalies(volumes[-1], volumes)
        
        return {
            "price_change_1h": price_change,
            "volume_change_1h": volume_change,
            "price_z_score": price_anomalies.get("z_score", 0),
            "volume_z_score": volume_anomalies.get("z_score", 0)
        }
    
    async def check_markets(self) -> List[MarketEvent]:
        """Check all watched markets for significant events."""
        events = []
        
        for pair in self.watched_pairs:
            try:
                # Get market data
                data = await self.fetch_market_data(pair)
                if not data:
                    continue
                    
                # Calculate indicators
                indicators = self.calculate_indicators(data)
                
                # Create event if significant
                if abs(indicators["price_z_score"]) > 2 or abs(indicators["volume_z_score"]) > 2:
                    events.append(MarketEvent(
                        symbol=pair,
                        price=data[-1]["close"],
                        volume=data[-1]["volume"],
                        timestamp=datetime.utcnow(),
                        indicators=indicators,
                        metadata={
                            "historical_data": data[-10:],  # Last 10 minutes
                            "anomaly_type": "price" if abs(indicators["price_z_score"]) > 2 else "volume"
                        }
                    ))
                    
            except Exception as e:
                print(f"Error monitoring {pair}: {str(e)}")
                continue
        
        return events