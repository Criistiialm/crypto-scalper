import logging
import os
from logging.handlers import RotatingFileHandler
import colorlog


def setup_logger(name: str = __name__, level: str = "INFO") -> logging.Logger:
    """Setup logger with file and console handlers"""

    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    # Create logs directory
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    # Console handler (colored)
    console_handler = colorlog.StreamHandler()
    console_handler.setFormatter(
        colorlog.ColoredFormatter(
            "%(log_color)s[%(asctime)s]%(reset)s %(name)s:%(levelname)s - %(message)s"
        )
    )
    logger.addHandler(console_handler)

    # File handler (rotating)
    file_handler = RotatingFileHandler(
        f"{log_dir}/crypto_scalper.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
    )
    file_handler.setFormatter(
        logging.Formatter("[%(asctime)s] %(name)s:%(levelname)s - %(message)s")
    )
    logger.addHandler(file_handler)

    return logger
