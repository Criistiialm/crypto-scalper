from datetime import datetime, timedelta
import pytz
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class TradingSession(Enum):
    LONDON = "LONDON"
    NEWYORK = "NEWYORK"
    OFF = "OFF"


class SessionManager:
    def __init__(self):
        self.tz_art = pytz.timezone("America/Argentina/Buenos_Aires")

    def get_current_session(self) -> TradingSession:
        """Get current trading session based on ART time (03:30 - 13:30)"""
        now_art = datetime.now(self.tz_art)
        
        hour = now_art.hour
        minute = now_art.minute
        time_in_minutes = hour * 60 + minute
        
        start_trade_min = 3 * 60 + 30  # 03:30 AM
        end_trade_min = 13 * 60 + 30   # 13:30 PM
        
        if start_trade_min <= time_in_minutes < end_trade_min:
            return TradingSession.LONDON
        else:
            return TradingSession.OFF

    def is_trading_hours(self) -> bool:
        """Check if current time is within trading hours"""
        return self.get_current_session() != TradingSession.OFF

    def get_time_until_trading(self) -> dict:
        """Get time until next trading session"""
        now_art = datetime.now(self.tz_art)
        
        start = now_art.replace(hour=3, minute=30, second=0, microsecond=0)
        if now_art < start:
            delta = start - now_art
            return {"minutes": int(delta.total_seconds() / 60), "session": "LONDON"}
            
        end = now_art.replace(hour=13, minute=30, second=0, microsecond=0)
        if now_art > end:
            tomorrow = now_art.replace(hour=3, minute=30, second=0, microsecond=0)
            tomorrow = tomorrow + timedelta(days=1)
            delta = tomorrow - now_art
            return {
                "minutes": int(delta.total_seconds() / 60),
                "session": "LONDON (tomorrow)",
            }
            
        return {"minutes": 0, "session": "TRADING"}


# Global instance
_session_manager = None


def get_session_manager() -> SessionManager:
    """Get session manager"""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager
