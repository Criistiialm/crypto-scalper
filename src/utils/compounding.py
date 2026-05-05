# src/utils/compounding.py
class CompoundingEngine:
    """
    Margen: 98% capital × 10x leverage
    TP1: +0.50% (cierra 50%)
    TP2: +1.00% (cierra 50%)
    Ganancia/trade: 7.35 USDT
    """

    def __init__(self, initial_capital=100, win_rate=0.80):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.win_rate = win_rate
        self.trades = []

    def calculate_trade_gain(self, capital, tp1_pct=0.005, tp2_pct=0.010):
        """
        Calcula ganancia exacta con split 50/50
        """
        margen = capital * 0.98
        posicion_total = margen * 10

        # 50% en TP1
        gain_tp1 = (posicion_total * 0.50) * tp1_pct

        # 50% en TP2
        gain_tp2 = (posicion_total * 0.50) * tp2_pct

        total_gain = gain_tp1 + gain_tp2

        return {
            "margen": margen,
            "posicion": posicion_total,
            "tp1_gain": gain_tp1,
            "tp2_gain": gain_tp2,
            "total_gain": total_gain,
            "roe": (total_gain / margen) * 100,
        }

    def simulate_month(self, trades_per_day=3, days=20):
        """
        Simula un mes de trading (20 días hábiles)
        """
        total_trades = trades_per_day * days
        winners = int(total_trades * self.win_rate)
        losers = total_trades - winners

        for i in range(total_trades):
            if i < winners:
                # Trade ganado
                gain_data = self.calculate_trade_gain(self.current_capital)
                self.current_capital += gain_data["total_gain"]
                pnl = gain_data["total_gain"]
            else:
                # Trade perdido (SL -0.50%)
                loss_margin = self.current_capital * 0.98
                pnl = -(loss_margin * 0.005)
                self.current_capital += pnl

            self.trades.append(
                {
                    "trade_num": i + 1,
                    "capital_before": self.current_capital - pnl,
                    "pnl": pnl,
                    "capital_after": self.current_capital,
                }
            )

        return {
            "initial_capital": self.initial_capital,
            "final_capital": self.current_capital,
            "total_gain": self.current_capital - self.initial_capital,
            "roi_pct": (
                (self.current_capital - self.initial_capital) / self.initial_capital
            )
            * 100,
            "total_trades": total_trades,
            "winners": winners,
            "losers": losers,
            "win_rate": self.win_rate * 100,
        }


# Uso:
engine = CompoundingEngine(initial_capital=100, win_rate=0.80)
results = engine.simulate_month()

print(f"""
📊 MONTH SIMULATION (80% Win Rate):
├─ Initial Capital: ${results["initial_capital"]:.2f}
├─ Final Capital: ${results["final_capital"]:.2f}
├─ Total Gain: ${results["total_gain"]:.2f}
├─ ROI: {results["roi_pct"]:.1f}%
├─ Trades: {results["total_trades"]} ({results["winners"]} win, {results["losers"]} loss)
└─ Win Rate: {results["win_rate"]:.0f}%
""")
