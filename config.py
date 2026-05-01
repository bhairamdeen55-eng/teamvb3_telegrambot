# config.py
from pydantic_settings import BaseSettings
from pydantic import Field, SecretStr, field_validator
from typing import Optional
from pathlib import Path


class Settings(BaseSettings):
    # ── Bot ───────────────────────────────────────────────────
    BOT_TOKEN: SecretStr = Field(..., validation_alias="BOT_TOKEN")
    BOT_USERNAME: Optional[str] = None
    ADMIN_IDS: list[int] = Field(default_factory=list, validation_alias="ADMIN_IDS")

    # ── Database ──────────────────────────────────────────────
    DATABASE_URL: str = Field(
        "sqlite+aiosqlite:///data/bot.db",
        validation_alias="DATABASE_URL"
    )
    DB_POOL_SIZE: int = Field(20, ge=1, le=100)
    DB_MAX_OVERFLOW: int = Field(10, ge=0, le=50)

    # ── AI / OpenAI ───────────────────────────────────────────
    AI_PROVIDER: str = Field("openai", validation_alias="AI_PROVIDER")
    AI_API_KEY: Optional[SecretStr] = Field(None, validation_alias="AI_API_KEY")
    AI_MODEL: str = Field("gpt-4o-mini", validation_alias="AI_MODEL")
    AI_TEMPERATURE: float = Field(0.3, ge=0.0, le=2.0)
    AI_MAX_TOKENS: int = Field(2048, ge=64, le=8192)
    VISION_MODEL: str = Field("gpt-4o-mini", validation_alias="VISION_MODEL")

    # ── Throttling ────────────────────────────────────────────
    THROTTLE_RATE: int = Field(3, ge=1, le=30)
    THROTTLE_BURST: int = Field(5, ge=1, le=50)

    # ── Webhook (optional) ────────────────────────────────────
    USE_WEBHOOK: bool = False
    WEBHOOK_URL: Optional[str] = None
    WEBHOOK_PORT: int = Field(8443, ge=1024, le=65535)
    WEBHOOK_SECRET: Optional[SecretStr] = None

    # ── Security (optional) ───────────────────────────────────
    ENCRYPTION_KEY: Optional[str] = None
    JWT_SECRET: Optional[str] = None
    SESSION_TTL: int = Field(86400, ge=300, le=2592000)

    # ── Paths ─────────────────────────────────────────────────
    DATA_DIR: Path = Field(Path("data"))
    LOG_DIR: Path = Field(Path("logs"))
    ASSETS_DIR: Path = Field(Path("assets"))

    # ── Logging ───────────────────────────────────────────────
    LOG_LEVEL: str = Field("INFO")
    SENTRY_DSN: Optional[str] = None

    # ── Subscription ──────────────────────────────────────────
    FREE_TRIAL_DAYS: int = Field(7, ge=1, le=365)
    SUBSCRIPTION_CHECK_INTERVAL: int = Field(3600, ge=300, le=86400)

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore",
        "validate_default": True,
    }

    # ── Validators ────────────────────────────────────────────

    @field_validator("ADMIN_IDS", mode="before")
    @classmethod
    def parse_admin_ids(cls, v):
        """
        Railway / .env se aane wale formats handle karta hai:
          - "123456789"            → [123456789]
          - "123456789,987654321"  → [123456789, 987654321]
          - "[123456789]"          → [123456789]   (brackets strip ho jayenge)
          - []  ya None            → []
        """
        if not v:
            return []
        if isinstance(v, (list, tuple)):
            return [int(x) for x in v if str(x).strip().lstrip("-").isdigit()]
        if isinstance(v, str):
            # brackets aur spaces strip karo
            v = v.strip().strip("[]")
            return [
                int(x.strip())
                for x in v.split(",")
                if x.strip().lstrip("-").isdigit()
            ]
        return []

    @field_validator("THROTTLE_BURST", mode="after")
    @classmethod
    def validate_throttle_burst(cls, v, info):
        throttle_rate = info.data.get("THROTTLE_RATE", 3)
        if v < throttle_rate:
            raise ValueError(
                f"THROTTLE_BURST ({v}) must be >= THROTTLE_RATE ({throttle_rate})"
            )
        return v

    @field_validator("LOG_LEVEL", mode="before")
    @classmethod
    def validate_log_level(cls, v):
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        v = str(v).upper()
        if v not in allowed:
            raise ValueError(f"LOG_LEVEL must be one of {allowed}")
        return v

    # ── Post Init ─────────────────────────────────────────────

    def model_post_init(self, __context) -> None:
        """Directories create karo agar exist nahi karti."""
        for directory in (self.DATA_DIR, self.LOG_DIR, self.ASSETS_DIR):
            try:
                directory.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                raise RuntimeError(f"Failed to create directory '{directory}': {e}")

    # ── Helper Properties ─────────────────────────────────────

    @property
    def bot_token(self) -> str:
        return self.BOT_TOKEN.get_secret_value()

    @property
    def ai_api_key(self) -> str | None:
        return self.AI_API_KEY.get_secret_value() if self.AI_API_KEY else None

    @property
    def webhook_secret_value(self) -> str | None:
        return self.WEBHOOK_SECRET.get_secret_value() if self.WEBHOOK_SECRET else None


# ── Load Settings ─────────────────────────────────────────────────────────────
try:
    settings = Settings()
except Exception as e:
    import sys
    print(f"❌ Configuration Error: {e}")
    sys.exit(1)
            
