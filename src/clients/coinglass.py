import aiohttp
import os
from typing import Dict, Optional


class CoinglassClient:
    """Coinglass API wrapper"""

    def __init__(self):
        self.api_key = os.getenv("COINGLASS_API_KEY")
        self.base_url = "https://api.coinglass.com/api/pro"

    async def get_funding_rate(self, symbol: str) -> Dict:
        """Get funding rate for symbol"""
        # TODO: Implement after May 11
        return {}

    async def get_open_interest(self, symbol: str) -> Dict:
        """Get open interest data"""
        # TODO: Implement after May 11
        return {}

    async def get_liquidations(self, symbol: str) -> Dict:
        """Get liquidation data"""
        # TODO: Implement after May 11
        return {}

    async def get_ls_ratio(self, symbol: str) -> Dict:
        """Get long/short ratio"""
        # TODO: Implement after May 11
        return {}
