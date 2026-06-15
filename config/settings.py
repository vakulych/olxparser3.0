from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List, Optional


class Settings(BaseSettings):
    BOT_TOKEN: str
    ADMIN_IDS: List[int] = []

    @field_validator("ADMIN_IDS", mode="before")
    @classmethod
    def parse_admin_ids(cls, v):
        if isinstance(v, list):
            return v
        if isinstance(v, int):
            return [v]
        if isinstance(v, str):
            return [int(x.strip()) for x in v.split(",") if x.strip()]
        return []

    DATABASE_URL: str = "postgresql+asyncpg://olxbot:olxpass@db:5432/olxbot"
    REDIS_URL: str = "redis://redis:6379/0"
    PROXIES: Optional[str] = None

    # 30 секунд — оптимально для миттєвої відправки
    PARSE_INTERVAL_SECONDS: int = 30
    MIN_FLIP_SCORE: int = 60

    LOG_LEVEL: str = "INFO"

    @property
    def proxy_list(self) -> List[str]:
        if self.PROXIES:
            return [p.strip() for p in self.PROXIES.split(",") if p.strip()]
        return []

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
