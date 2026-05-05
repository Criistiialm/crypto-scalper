from datetime import datetime
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
        self.tz_utc = pytz.utc

    def get_current_session(self) -> TradingSession:
        """Get current trading session"""
        now_art = datetime.now(self.tz_art)
        now_utc = now_art.astimezone(self.tz_utc)

        hour = now_utc.hour
        minute = now_utc.minute

        current_time = hour + minute / 60

        # LONDON: 8:30 AM - 4:00 PM UTC (8.5 - 16.0)
        if 8.5 <= current_time < 16.0:
            return TradingSession.LONDON

        # NY: 1:30 PM - 4:30 PM UTC (13.5 - 16.5)
        # But we only trade for 3h = until 4:30 PM UTC (16.5)
        elif 13.5 <= current_time < 16.5:
            return TradingSession.NEWYORK

        else:
            return TradingSession.OFF

    def is_trading_hours(self) -> bool:
        """Check if current time is within trading hours"""
        session = self.get_current_session()
        return session != TradingSession.OFF

    def get_time_until_trading(self) -> dict:
        """Get time until next trading session"""
        now_art = datetime.now(self.tz_art)

        # Start: 3:30 AM ART
        start = now_art.replace(hour=3, minute=30, second=0, microsecond=0)

        if now_art < start:
            delta = start - now_art
            return {"minutes": int(delta.total_seconds() / 60), "session": "LONDON"}

        # If past 1:30 PM ART, next session is tomorrow
        end = now_art.replace(hour=13, minute=30, second=0, microsecond=0)

        if now_art > end:
            tomorrow = now_art.replace(hour=3, minute=30, second=0, microsecond=0)
            tomorrow = tomorrow.replace(day=tomorrow.day + 1)
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
