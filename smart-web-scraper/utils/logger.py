"""
Sets up a logger that writes to the console and to a timestamped file under
logs/. Every scraper run gets its own log file so past runs aren't
overwritten, which makes it easy to go back and check what happened during
a specific scrape.
"""
import logging
from datetime import datetime

from config.settings import LOGS_DIR, LOG_LEVEL


def get_logger(name: str = "smart_web_scraper") -> logging.Logger:
    logger = logging.getLogger(name)

    if logger.handlers:
        # Logger already configured (avoids duplicate handlers when
        # get_logger is called from multiple modules).
        return logger

    logger.setLevel(LOG_LEVEL)

    log_format = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_format)
    logger.addHandler(console_handler)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file_path = f"{LOGS_DIR}/scrape_{timestamp}.log"
    file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
    file_handler.setFormatter(log_format)
    logger.addHandler(file_handler)

    logger.log_file_path = log_file_path
    return logger
