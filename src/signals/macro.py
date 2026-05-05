from typing import Dict


class MacroSignals:
    """Compute macro signals from Coinglass data"""

    def __init__(self):
        self.weights = {
            "funding": 0.30,
            "oi": 0.20,
            "liquidations": 0.25,
            "ls_ratio": 0.25,
        }

    def compute_funding_signal(self, funding_rate: float) -> float:
        """Contrarian: extremes = opportunities"""
        # TODO: Implement after May 11
        return 0.0

    def compute_oi_signal(self, oi_change: float) -> float:
        """Open interest trend signal"""
        # TODO: Implement after May 11
        return 0.0

    def compute_liquidation_signal(self, long_liq: float, short_liq: float) -> float:
        """Liquidation pressure signal"""
        # TODO: Implement after May 11
        return 0.0

    def compute_ls_signal(self, ls_ratio: float) -> float:
        """Long/Short ratio contrarian signal"""
        # TODO: Implement after May 11
        return 0.0

    def compute_macro_score(self, data: Dict) -> float:
        """Combine all macro signals"""
        # TODO: Implement after May 11
        return 0.0
