import pytest
import asyncio
from src.agent import HighProbabilityScalper
from src.utils.session import get_session_manager
from src.utils.compounding import CompoundingEngine


@pytest.mark.asyncio
async def test_agent_initialization():
    """Test agent initializes correctly"""
    agent = HighProbabilityScalper()
    assert agent.capital == 100.0
    assert agent.leverage == 10
    assert agent.confluence_min == 0.75


def test_session_manager():
    """Test session manager"""
    session_mgr = get_session_manager()
    session = session_mgr.get_current_session()
    assert session is not None


def test_compounding_engine():
    """Test compounding calculations"""
    engine = CompoundingEngine(initial_capital=100)

    # Test winning trade
    win_result = engine.calculate_winning_trade(100)
    assert win_result["total_gain"] > 0
    assert win_result["roe"] > 0

    # Test losing trade
    loss_result = engine.calculate_losing_trade(100)
    assert loss_result["loss"] > 0
    assert loss_result["roe"] < 0


def test_month_simulation():
    """Test month simulation"""
    engine = CompoundingEngine(initial_capital=100)
    results = engine.simulate_month(win_rate=0.80)

    assert results["total_trades"] > 0
    assert results["winners"] > 0
    assert results["roi_pct"] > 0  # 80% win rate = ganancia
