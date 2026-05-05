from typing import Dict


class TechnicalSignals:
    """Compute technical signals from Bybit data"""

    def __init__(self):
        self.weights = {"adx": 0.35, "cvd": 0.35, "price": 0.20, "order_book": 0.10}

    def compute_adx(self, price_data: Dict) -> float:
        """Calculate ADX (trend strength)"""
        # TODO: Implement after May 11
        return 0.0

    def compute_cvd(self, volume_data: Dict) -> float:
        """Cumulative Volume Delta"""
        # TODO: Implement after May 11
        return 0.0

    def compute_price_signal(self, price_data: Dict) -> float:
        """Price vs MA20 signal"""
        # TODO: Implement after May 11
        return 0.0

    def compute_order_book_signal(self, order_book: Dict) -> float:
        """Order book imbalance signal"""
        # TODO: Implement after May 11
        return 0.0

    def compute_technical_score(self, data: Dict) -> float:
        """Combine all technical signals"""
        # TODO: Implement after May 11
        return 0.0
