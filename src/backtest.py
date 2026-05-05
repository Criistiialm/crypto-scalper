import asyncio
import logging
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

from src.agent import HighProbabilityScalper

load_dotenv()
logger = logging.getLogger(__name__)

api_key = os.getenv("BYBIT_API_KEY")
api_secret = os.getenv("BYBIT_API_SECRET")


async def run_backtest(weeks: int = 4):
    """
    Run backtest for N weeks

    Args:
        weeks: Number of weeks to backtest (default 4)
    """
    logger.info(f"🚀 Starting {weeks}-week backtest...")

    agent = HighProbabilityScalper()

    # Backtest 4 weeks (20 trading days)
    trading_days = weeks * 5

    for day in range(trading_days):
        date = datetime.now() - timedelta(days=trading_days - day)

        logger.info(f"📅 Day {day + 1}/{trading_days}: {date.date()}")

        # Simulate LONDON and NY sessions
        for session in ["LONDON", "NEWYORK"]:
            result = await agent.run_trading_cycle(session, historical_date=date)
            logger.info(f"   {session}: {len(result.get('trades', []))} trades")

    # Print summary
    metrics = {
        "total_trades": len(agent.trades),
        "winners": len([t for t in agent.trades if t.get("pnl", 0) > 0]),
        "losers": len([t for t in agent.trades if t.get("pnl", 0) <= 0]),
        "final_capital": agent.capital,
    }

    logger.info(f"""
╔════════════════════════════════════════╗
║         BACKTEST SUMMARY ({weeks} WEEKS)        ║
╚════════════════════════════════════════╝
├─ Total Trades: {metrics["total_trades"]}
├─ Winners: {metrics["winners"]}
├─ Losers: {metrics["losers"]}
├─ Win Rate: {(metrics["winners"] / max(metrics["total_trades"], 1) * 100):.1f}%
├─ Final Capital: {metrics["final_capital"]:.2f} USDT
└─ ROI: {((metrics["final_capital"] - 100) / 100 * 100):.1f}%
    """)


if __name__ == "__main__":
    asyncio.run(run_backtest(weeks=4))
