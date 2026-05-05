import aiohttp
import os
from typing import Dict, List


class BybitClient:
    """Bybit API wrapper"""

    def __init__(self, testnet: bool = True):
        self.testnet = testnet
        self.api_key = os.getenv(
            "BYBIT_DEMO_API_KEY" if testnet else "BYBIT_LIVE_API_KEY"
        )
        self.api_secret = os.getenv(
            "BYBIT_DEMO_API_SECRET" if testnet else "BYBIT_LIVE_API_SECRET"
        )
        self.base_url = (
            "https://testnet.bybit.com/v5" if testnet else "https://api.bybit.com/v5"
        )

    async def get_ohlcv(self, symbol: str, timeframe: str = "1m") -> List[Dict]:
        """Get OHLCV candlesticks"""
        # TODO: Implement after May 11
        return []

    async def get_order_book(self, symbol: str, depth: int = 20) -> Dict:
        """Get order book"""
        # TODO: Implement after May 11
        return {}

    async def place_order(self, symbol: str, side: str, size: float) -> Dict:
        """Place market order"""
        # TODO: Implement after May 11
        return {}

    async def get_positions(self) -> List[Dict]:
        """Get open positions"""
        # TODO: Implement after May 11
        return []
