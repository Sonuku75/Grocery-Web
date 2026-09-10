import logging
import sys
import re
from typing import Any, Dict

# Sensitive fields to mask in log messages and payloads
SENSITIVE_PATTERNS = [
    re.compile(r'"password"\s*:\s*"[^"]*"', re.IGNORECASE),
    re.compile(r'"token"\s*:\s*"[^"]*"', re.IGNORECASE),
    re.compile(r'"secret"\s*:\s*"[^"]*"', re.IGNORECASE),
    re.compile(r'"authorization"\s*:\s*"[^"]*"', re.IGNORECASE),
    re.compile(r'Bearer\s+[A-Za-z0-9\-\._~\+\/]+=*', re.IGNORECASE),
]

def mask_sensitive_data(message: str) -> str:
    masked = message
    for pattern in SENSITIVE_PATTERNS:
        masked = pattern.sub('"[REDACTED]"', masked)
    return masked

class SensitiveDataFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = mask_sensitive_data(record.msg)
        return True

def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """
    Configures structured console logging with timestamp, level, and sensitive data masking.
    """
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    handler.addFilter(SensitiveDataFilter())

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Avoid duplicate handlers
    if not root_logger.handlers:
        root_logger.addHandler(handler)
    else:
        root_logger.handlers = [handler]

    # Specific logger for Cartify application
    logger = logging.getLogger("cartify")
    return logger

logger = setup_logging()
