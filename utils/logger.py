# utils/logger.py
import sys
from pathlib import Path
from loguru import logger


def setup_logging(log_level: str = "INFO", log_file: str = "logs/bot.log") -> None:
    """Loguru logging setup — Railway aur local dono ke liye."""

    # Pehle default handler remove karo
    logger.remove()

    # ── Console Handler ───────────────────────────────────────
    # NOTE: {time} mein quotes nahi hone chahiye — yeh KeyError fix hai
    logger.add(
        sys.stdout,
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{line}</cyan> | "
               "<level>{message}</level>",
        colorize=True,
    )

    # ── File Handler ──────────────────────────────────────────
    try:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        logger.add(
            log_file,
            level=log_level,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{line} | {message}",
            rotation="10 MB",
            retention="7 days",
            compression="zip",
            encoding="utf-8",
        )
    except Exception as e:
        logger.warning(f"File logging setup failed: {e} — only console logging active")

    logger.info(f"Logging initialized | Level: {log_level} | File: {log_file}")
    
