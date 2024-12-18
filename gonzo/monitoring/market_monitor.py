"""Cryptocurrency market monitoring implementation."""
import os
from typing import Dict, Any, List, Tuple
from datetime import datetime, timedelta
import aiohttp
from pydantic import ValidationError

from ..state_management import UnifiedState, MarketData
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
    
    async def fetch_market_data(self, symbol: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """Fetch current market data and history for a symbol."""
        # Current price endpoint
        current_url = f"{self.base_url}/price"
        history_url = f"{self.base_url}/v2/histominute"
        
        fsym = symbol.split("/")[0]
        params_current = {
            "fsym": fsym,
            "tsyms": "USD"
        }
        params_history = {
            "fsym": fsym,
            "tsym": "USD",
            "limit": 60  # Last hour
        }
        headers = {"authorization": f"Apikey {self.api_key}"}
        
        async with aiohttp.ClientSession() as session:
            # Fetch current price
            async with session.get(current_url, params=params_current, headers=headers) as response:
                if response.status != 200:
                    raise Exception(f"API Error: {await response.text()}")
                current_data = await response.json()
            
            # Fetch historical data
            async with session.get(history_url, params=params_history, headers=headers) as response:
                if response.status != 200:
                    raise Exception(f"API Error: {await response.text()}")
                historical_data = await response.json()
                
        return current_data, historical_data.get("Data", {}).get("Data", [])
    
    def calculate_24h_change(self, historical_data: List[Dict[str, Any]]) -> float:
        """Calculate 24-hour price change percentage."""
        if not historical_data or len(historical_data) < 2:
            return 0.0
        
        start_price = historical_data[0].get("close", 0)
        end_price = historical_data[-1].get("close", 0)
        
        if start_price == 0:
            return 0.0
            
        return ((end_price - start_price) / start_price) * 100
    
    async def update_market_state(self, state: UnifiedState) -> UnifiedState:
        """Update market data in the unified state."""
        for pair in self.watched_pairs:
            try:
                # Fetch current and historical data
                current_data, historical_data = await self.fetch_market_data(pair)
                
                if not current_data or "USD" not in current_data:
                    continue
                
                # Calculate metrics
                current_price = float(current_data["USD"])
                current_volume = historical_data[-1].get("volumeto", 0) if historical_data else 0
                change_24h = self.calculate_24h_change(historical_data)
                
                # Create MarketData instance
                market_data = MarketData(
                    price=current_price,
                    timestamp=datetime.utcnow(),
                    volume=current_volume,
                    change_24h=change_24h,
                    symbol=pair
                )
                
                # Update state
                state.market_data[pair] = market_data
                
                # Check for significant events
                if abs(change_24h) > 5.0:  # 5% change threshold
                    event = MarketEvent(
                        symbol=pair,
                        price=current_price,
                        volume=current_volume,
                        timestamp=datetime.utcnow(),
                        indicators={"price_change_24h": change_24h},
                        metadata={"historical_data": historical_data[-10:]}  # Last 10 minutes
                    )
                    state.narrative.market_events.append(event.__dict__)
                    state.narrative.pending_analyses = True
                
            except ValidationError as e:
                print(f"Validation error for {pair}: {str(e)}")
                state.api_errors.append(f"Market data validation error for {pair}: {str(e)}")
                continue
            except Exception as e:
                print(f"Error monitoring {pair}: {str(e)}")
                state.api_errors.append(f"Market monitoring error for {pair}: {str(e)}")
                continue
        
        return state