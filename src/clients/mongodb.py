import os

from pymongo import MongoClient

from pymongo.errors import ConnectionFailure

import logging

logger = logging.getLogger(__name__)


class MongoDBClient:
    def __init__(self):

        self.uri = os.getenv("MONGODB_URI")

        self.db_name = os.getenv("MONGODB_DATABASE", "crypto-scalper")

        self.client = None

        self.db = None

    def connect(self):
        """Connect to MongoDB"""

        try:
            self.client = MongoClient(self.uri, serverSelectionTimeoutMS=5000)

            self.client.admin.command("ping")

            self.db = self.client[self.db_name]

            logger.info(f"✅ MongoDB connected: {self.db_name}")

            self._create_indexes()

            return True

        except ConnectionFailure as e:
            logger.error(f"❌ MongoDB connection failed: {e}")

            return False

    def _create_indexes(self):
        """Create required indexes"""

        # Trades collection

        self.db.trades.create_index([("timestamp", -1)])

        self.db.trades.create_index([("symbol", 1), ("timestamp", -1)])

        self.db.trades.create_index([("status", 1)])

        # Signals collection

        self.db.signals.create_index([("timestamp", -1)])

        self.db.signals.create_index([("symbol", 1)])

        # Candles collection

        self.db.candles.create_index([("symbol", 1), ("timestamp", -1)])

        # Metrics collection

        self.db.metrics.create_index([("date", -1)])

        logger.info("✅ MongoDB indexes created")

    def disconnect(self):
        """Close MongoDB connection"""

        if self.client:
            self.client.close()

            logger.info("✅ MongoDB disconnected")

    def insert_trade(self, trade_data: dict) -> str:
        """Insert trade record"""

        result = self.db.trades.insert_one(trade_data)

        return str(result.inserted_id)

    def get_trades(self, symbol: str = None, limit: int = 100):
        """Get trades (optionally filtered by symbol)"""

        query = {"symbol": symbol} if symbol else {}

        return list(self.db.trades.find(query).sort("timestamp", -1).limit(limit))

    def insert_signal(self, signal_data: dict) -> str:
        """Insert signal record"""

        result = self.db.signals.insert_one(signal_data)

        return str(result.inserted_id)

    def insert_metrics(self, metrics_data: dict) -> str:
        """Insert metrics record"""

        result = self.db.metrics.insert_one(metrics_data)

        return str(result.inserted_id)


# Global instance

_mongo_client = None


def get_mongo_client() -> MongoDBClient:
    """Get or create MongoDB client"""

    global _mongo_client

    if _mongo_client is None:
        _mongo_client = MongoDBClient()

        _mongo_client.connect()

    return _mongo_client
