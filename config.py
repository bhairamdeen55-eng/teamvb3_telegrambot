# config.py
from pydantic_settings import BaseSettings
from pydantic import Field, SecretStr
from typing import Optional
from pathlib import Path

class Settings(BaseSettings):
    # Bot
    BOT_TOKEN: SecretStr = Field(..., validation_alias="BOT_TOKEN")
    BOT_USERNAME: Optional[str] = None
    ADMIN_IDS: list[int] = Field(default_factory=list, validation_alias="ADMIN_IDS")
    
    # Database
    DATABASE_URL: str = Field("sqlite+aiosqlite:///data/bot.db", validation_alias="DATABASE_URL")
    DB_POOL_SIZE: int = Field(20, ge=1, le=100)
    DB_MAX_OVERFLOW: int = Field(10, ge=0)
    
    # AI / Vision
    AI_PROVIDER: str = Field("openai", validation_alias="AI_PROVIDER")
    AI_API_KEY: Optional[SecretStr] = Field(None, validation_alias="AI_API_KEY")
    AI_MODEL: str = Field("gpt-4o-mini", validation_alias="AI_MODEL")
    AI_TEMPERATURE: float = Field(0.3, ge=0.0, le=2.0)
    AI_MAX_TOKENS: int = Field(2048, ge=64, le=8192)
    VISION_MODEL: str = Field("gpt-4o-mini", validation_alias="VISION_MODEL")
    
    # Throttling
    THROTTLE_RATE: int = Field(3, ge=1, le=30)
    THROTTLE_BURST: int = Field(5, ge=1, le=50)
    
    # Webhook
    USE_WEBHOOK: bool = False
    WEBHOOK_URL: Optional[str] = None
    WEBHOOK_PORT: int = Field(8443, ge=1024, le=65535)
    WEBHOOK_SECRET: Optional[SecretStr] = None
    
    # Security
    ENCRYPTION_KEY: Optional[str] = None
    JWT_SECRET: Optional[str] = None
    SESSION_TTL: int = 86400
    
    # Paths
    DATA_DIR: Path = Field(Path("data"))
    LOG_DIR: Path = Field(Path("logs"))
    ASSETS_DIR: Path = Field(Path("assets"))
    
    # Logging
    LOG_LEVEL: str = "INFO"
    SENTRY_DSN: Optional[str] = None
    
    # Subscription
    FREE_TRIAL_DAYS: int = 7
    SUBSCRIPTION_CHECK_INTERVAL: int = 3600

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore",
        "validate_default": True,
    }

    def model_post_init(self, __context):
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.LOG_DIR.mkdir(parents=True, exist_ok=True)
        if isinstance(self.ADMIN_IDS, str):
            self.ADMIN_IDS = [int(x.strip()) for x in self.ADMIN_IDS.split(",") if x.strip().isdigit()]
        if self.THROTTLE_RATE > self.THROTTLE_BURST:
            raise ValueError("THROTTLE_BURST must be >= THROTTLE_RATE")

settings = Settings()
