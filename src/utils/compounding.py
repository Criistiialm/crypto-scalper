import logging

logger = logging.getLogger(__name__)


class CompoundingEngine:
    """
    Calculate exact profit/loss with compounding

    Specs:
    - Margin: 98% × 10x leverage
    - TP1: +0.50% (50% cierra) = 2.45 USDT
    - TP2: +1.00% (50% cierra) = 4.90 USDT
    - Total per winning trade: 7.35 USDT
    - Loss (SL): -0.50% = -4.90 USDT
    """

    def __init__(self, initial_capital: float = 100.0, leverage: int = 10):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.leverage = leverage
        self.compounding_pct = 0.98
        self.sl_pct = 0.005
        self.tp1_pct = 0.005
        self.tp2_pct = 0.010
        self.trades = []

    def calculate_winning_trade(self, capital: float) -> dict:
        """Calculate exact gains for winning trade (50/50 split)"""
        margen = capital * self.compounding_pct
        posicion_total = margen * self.leverage

        # TP1: 50% de posición @ +0.50%
        posicion_tp1 = posicion_total * 0.50
        ganancia_tp1 = posicion_tp1 * self.tp1_pct

        # TP2: 50% de posición @ +1.00%
        posicion_tp2 = posicion_total * 0.50
        ganancia_tp2 = posicion_tp2 * self.tp2_pct

        ganancia_total = ganancia_tp1 + ganancia_tp2
        roe = (ganancia_total / margen) * 100

        return {
            "margen": margen,
            "posicion_total": posicion_total,
            "tp1_gain": ganancia_tp1,
            "tp2_gain": ganancia_tp2,
            "total_gain": ganancia_total,
            "roe": roe,
        }

    def calculate_losing_trade(self, capital: float) -> dict:
        """Calculate loss for SL hit (-0.50%)"""
        margen = capital * self.compounding_pct
        posicion_total = margen * self.leverage

        perdida = posicion_total * self.sl_pct
        roe_loss = -(perdida / margen) * 100

        return {
            "margen": margen,
            "posicion_total": posicion_total,
            "loss": perdida,
            "roe": roe_loss,
        }

    def execute_trade(self, is_winning: bool) -> dict:
        """Execute trade (win or loss) and update capital"""
        if is_winning:
            result = self.calculate_winning_trade(self.current_capital)
            self.current_capital += result["total_gain"]
            pnl = result["total_gain"]
        else:
            result = self.calculate_losing_trade(self.current_capital)
            self.current_capital -= result["loss"]
            pnl = -result["loss"]

        trade_record = {
            "trade_num": len(self.trades) + 1,
            "capital_before": self.current_capital - pnl,
            "pnl": pnl,
            "capital_after": self.current_capital,
            "is_winning": is_winning,
        }

        self.trades.append(trade_record)
        return trade_record

    def simulate_month(
        self, win_rate: float = 0.80, trades_per_day: int = 3, days: int = 20
    ) -> dict:
        """Simulate one month of trading"""
        total_trades = trades_per_day * days
        num_winners = int(total_trades * win_rate)
        num_losers = total_trades - num_winners

        # Shuffle: winners y losers aleatorios
        trades_sequence = [True] * num_winners + [False] * num_losers
        import random

        random.shuffle(trades_sequence)

        for is_winning in trades_sequence:
            self.execute_trade(is_winning)

        total_pnl = self.current_capital - self.initial_capital

        return {
            "initial_capital": self.initial_capital,
            "final_capital": self.current_capital,
            "total_pnl": total_pnl,
            "roi_pct": (total_pnl / self.initial_capital) * 100,
            "total_trades": total_trades,
            "winners": num_winners,
            "losers": num_losers,
            "win_rate": win_rate * 100,
            "avg_gain_per_winning_trade": total_pnl / num_winners
            if num_winners > 0
            else 0,
        }


# Example usage
if __name__ == "__main__":
    engine = CompoundingEngine(initial_capital=100)
    results = engine.simulate_month(win_rate=0.80, trades_per_day=3, days=20)

    print(f"""
╔════════════════════════════════════════╗
║       MONTH SIMULATION (80% WR)        ║
╚════════════════════════════════════════╝
├─ Initial Capital: \${results["initial_capital"]:.2f}
├─ Final Capital: \${results["final_capital"]:.2f}
├─ Total PnL: +\${results["total_pnl"]:.2f}
├─ ROI: +{results["roi_pct"]:.1f}%
├─ Total Trades: {results["total_trades"]}
├─ Winners: {results["winners"]}
├─ Losers: {results["losers"]}
├─ Win Rate: {results["win_rate"]:.1f}%
└─ Avg Gain/Trade: \${results["avg_gain_per_winning_trade"]:.2f}
    """)
