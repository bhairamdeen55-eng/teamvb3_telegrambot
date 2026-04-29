# utils/logger.py
import sys
import json
import logging
from pathlib import Path
from loguru import logger
from config import settings

class InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
        frame, depth = sys._getframe(6), 6
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1
        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())

def setup_logging() -> None:
    log_path = settings.LOG_DIR / "bot.log"
    logger.remove()
    
    # Console
    logger.add(
        sys.stdout,
        level=settings.LOG_LEVEL,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan> | <level>{message}</level>",
        colorize=True,
    )
    
    # File (JSON)
    logger.add(
        log_path,
        level=settings.LOG_LEVEL,
        format=lambda r: json.dumps({
            "timestamp": r["time"].isoformat(),
            "level": r["level"].name,
            "module": r["name"],
            "function": r["function"],
            "line": r["line"],
            "message": r["message"],
        }, default=str),
        rotation="100 MB",
        retention="30 days",
        compression="gz",
    )
    
    # Intercept standard logging
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    
    # Silence noisy libs
    logging.getLogger("aiogram").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    
    logger.info("Logging initialized | Level: %s | File: %s", settings.LOG_LEVEL, log_path)
