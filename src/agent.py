import asyncio
import logging
import os
import pandas as pd
from typing import TypedDict, List, Optional
from datetime import datetime
from dotenv import load_dotenv

from langgraph.graph import StateGraph, END
from langsmith import Client as LangSmithClient
from src.utils.session import get_session_manager, TradingSession
from src.clients.mongodb import get_mongo_client
from src.utils.compounding import CompoundingEngine

from src.clients.bybit import BybitClient
from src.clients.coinglass import CoinglassClient
from src.signals.smc_engine import SMCEngine

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)


# ===== STATE DEFINITION =====
class TradingState(TypedDict):
    """State for trading graph"""

    symbols: List[str]
    session: str
    timestamp: str
    coinglass_data: dict
    price_data: dict
    macro_signals: dict
    technical_signals: dict
    order_flow_signals: dict
    confluence_score: dict
    decisions: dict
    execution_results: dict
    trades: list
    smc_analysis: dict # To pass the SMC dataframe output
    entry_signal: bool


# ===== AGENT CLASS =====
class HighProbabilityScalper:
    """
    High-probability scalping bot

    Specs:
    - Margin: 98% × 10x leverage
    - TP1: +0.50% (50% cierra)
    - TP2: +1.00% (50% cierra)
    - Ganancia/trade: 7.35 USDT
    - Win Rate Target: 80%
    - Confluence: >= 0.75
    """

    def __init__(self):
        self.capital = float(os.getenv("INITIAL_CAPITAL", 100))
        self.leverage = int(os.getenv("LEVERAGE", 10))
        self.compounding_pct = 0.98
        self.sl_pct = 0.005
        self.tp1_pct = 0.005
        self.tp2_pct = 0.010
        self.confluence_min = float(os.getenv("CONFLUENCE_THRESHOLD", 0.75))
        self.win_rate_target = float(os.getenv("WIN_RATE_TARGET", 0.80))
        self.trades: List[dict] = []
        self.mode = os.getenv("MODE", "BACKTEST")
        self.session_manager = get_session_manager()
        self.mongo_client = get_mongo_client()
        self.compounding = CompoundingEngine(self.capital, self.leverage)
        
        self.bybit = BybitClient()
        self.coinglass = CoinglassClient()

        # LangSmith tracing (optional)
        try:
            self.langsmith_client = LangSmithClient()
        except Exception:
            self.langsmith_client = None

        # Build graph
        self.graph = self._build_graph()

        logger.info(f"✅ Agent initialized: {self.mode} mode")
        logger.info(f"   Capital: {self.capital} USDT")
        logger.info(f"   Leverage: {self.leverage}x")
        logger.info(f"   Confluence threshold: {self.confluence_min}")

    def _build_graph(self) -> StateGraph:
        """Build LangGraph trading graph"""
        builder = StateGraph(TradingState)

        # Add nodes
        builder.add_node("ingest_coinglass", self.ingest_coinglass)
        builder.add_node("ingest_bybit", self.ingest_bybit)
        builder.add_node("compute_signals", self.compute_signals)
        builder.add_node("calculate_confluence", self.calculate_confluence)
        builder.add_node("execute", self.execute_trades)
        builder.add_node("monitor", self.monitor_trades)
        builder.add_node("log_metrics", self.log_metrics)

        # Add edges
        builder.set_entry_point("ingest_coinglass")
        builder.add_edge("ingest_coinglass", "ingest_bybit")
        builder.add_edge("ingest_bybit", "compute_signals")
        builder.add_edge("compute_signals", "calculate_confluence")
        
        # Conditional Execution
        builder.add_conditional_edges(
            "calculate_confluence",
            lambda s: "execute" if s.get("entry_signal", False) else "monitor",
        )
        builder.add_edge("execute", "monitor")
        builder.add_edge("monitor", "log_metrics")
        builder.add_edge("log_metrics", END)

        return builder.compile()

    async def ingest_coinglass(self, state: TradingState) -> TradingState:
        """Ingest Coinglass data (macro signals)"""
        logger.info(f"📥 Ingesting Coinglass data...")
        
        symbol = state["symbols"][0]
        # Mock / Placeholder call until May 11
        funding = await self.coinglass.get_funding_rate(symbol)
        oi = await self.coinglass.get_open_interest(symbol)
        
        state["coinglass_data"] = {
            "funding": funding,
            "oi": oi,
            "retail_sentiment": "long" # Mock for "Trampa Institucional"
        }
        return state

    async def ingest_bybit(self, state: TradingState) -> TradingState:
        """Ingest Bybit data (technical signals)"""
        logger.info(f"📥 Ingesting Bybit data...")
        symbol = state["symbols"][0]
        start_time = state.get("timestamp")
        ohlcv = await self.bybit.get_ohlcv(symbol, "15m", start_time=start_time)
        
        # Parse data into DataFrame for SMCEngine
        if not ohlcv:
            # Fallback for testing: Generate empty valid dataframe
            df = pd.DataFrame(columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        else:
            df = pd.DataFrame(ohlcv)
            
        state["price_data"] = {"df": df}
        return state

    async def compute_signals(self, state: TradingState) -> TradingState:
        """Compute all signals using SMCEngine"""
        logger.info(f"🔍 Computing signals (SMC Engine)...")
        df = state["price_data"].get("df", pd.DataFrame())
        
        if not df.empty:
            engine = SMCEngine(df)
            analyzed_df = engine.analyze()
            
            # Save latest state for confluence calculation
            latest = analyzed_df.iloc[-1]
            state["smc_analysis"] = {
                "is_tradable": bool(latest.get('is_tradable', False)),
                "bos": int(latest.get('bos', 0)),
                "choch": int(latest.get('choch', 0)),
                "fvg_bullish": bool(latest.get('fvg_bullish', False)),
                "fvg_bearish": bool(latest.get('fvg_bearish', False)),
            }
        else:
            state["smc_analysis"] = {
                "is_tradable": False, "bos": 0, "choch": 0,
                "fvg_bullish": False, "fvg_bearish": False
            }
            
        return state

    async def calculate_confluence(self, state: TradingState) -> TradingState:
        """
        Calculate confluence score
        Skill 4: Market Maker Trap & Liquidity Hunter
        """
        logger.info(f"📊 Calculating confluence...")
        smc = state.get("smc_analysis", {})
        cg = state.get("coinglass_data", {})
        
        entry = False
        confluence = 0.0
        
        # 1. Time & Session Validation
        if not smc.get("is_tradable", False):
            logger.info("  -> Fuera de sesión. No tradable.")
            state["entry_signal"] = False
            return state
            
        # 2. Institutional Trap & SMC Logic
        # We want to go SHORT if retail is heavily LONG
        if cg.get("retail_sentiment") == "long":
            # Looking for SHORT setups
            if smc.get("choch") == -1 or smc.get("bos") == -1:
                confluence += 0.5
            if smc.get("fvg_bearish"):
                confluence += 0.5
                
            if confluence >= self.confluence_min:
                logger.info("  -> Trampa institucional bajista detectada (SHORT)")
                entry = True

        state["confluence_score"] = {"score": confluence}
        state["entry_signal"] = entry
        
        return state

    async def execute_trades(self, state: TradingState) -> TradingState:
        """Execute trades if confluence >= threshold"""
        logger.info(f"🚀 Executing trades...")
        symbol = state["symbols"][0]
        # TODO: Implement Bybit actual execution logic after May 11
        # await self.bybit.place_order(symbol, "Sell", size=...)
        
        # Simulamos ejecución y PnL usando el CompoundingEngine para el Backtest
        import random
        is_winner = random.random() < self.win_rate_target
        trade_result = self.compounding.execute_trade(is_winning=is_winner)
        self.capital = self.compounding.current_capital
        
        # Guardamos en la lista global de trades del agente
        self.trades.append(trade_result)
        
        state["execution_results"] = {
            "status": "executed (simulated)",
            "trade": trade_result
        }
        return state

    async def monitor_trades(self, state: TradingState) -> TradingState:
        """Monitor open trades for SL/TP"""
        logger.info(f"👁️ Monitoring trades...")
        return state

    async def log_metrics(self, state: TradingState) -> TradingState:
        """Log metrics to MongoDB Memory Bank"""
        logger.info(f"📈 Logging metrics to Memory Bank...")
        
        signal_data = {
            "timestamp": state["timestamp"],
            "symbols": state["symbols"],
            "session": state["session"],
            "smc_data": state.get("smc_analysis", {}),
            "coinglass_data": state.get("coinglass_data", {}),
            "confluence": state.get("confluence_score", {}),
            "entry_triggered": state.get("entry_signal", False),
            "execution": state.get("execution_results", {})
        }
        
        # Log to MongoDB
        try:
            self.mongo_client.insert_signal(signal_data)
        except Exception as e:
            logger.error(f"  -> Error saving to MongoDB: {e}")
            
        return state

    async def run_trading_cycle(self, session: str, historical_date: Optional[datetime] = None) -> dict:
        """Execute one full trading cycle"""
        timestamp_str = historical_date.isoformat() if historical_date else datetime.now().isoformat()
        initial_state = TradingState(
            symbols=["BTC/USDT"],
            session=session,
            timestamp=timestamp_str,
            coinglass_data={},
            price_data={},
            macro_signals={},
            technical_signals={},
            order_flow_signals={},
            confluence_score={},
            decisions={},
            execution_results={},
            trades=[],
            smc_analysis={},
            entry_signal=False
        )

        logger.info(f"🔄 Starting trading cycle: {session}")
        result = await self.graph.ainvoke(initial_state)
        logger.info(f"✅ Trading cycle complete")

        return result


# ===== MAIN =====
async def main():
    agent = HighProbabilityScalper()

    # Check session
    if not agent.session_manager.is_trading_hours():
        logger.info("Actualmente fuera de horario de trading (03:30 - 13:30 ART).")
        # Could sleep here in production
        
    session_name = agent.session_manager.get_current_session().name

    # Run trading cycle
    result = await agent.run_trading_cycle(session_name)
    logger.info(f"Cycle Result: {result.get('entry_signal', False)}")


if __name__ == "__main__":
    asyncio.run(main())
