import os
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Parametros de conexao que sao sintaxe libpq/psycopg2 e nao sao aceitos pelo
# asyncpg. Devem ser removidos da query string antes de entregar a URL para
# o create_async_engine (o SSL e ligado via connect_args no database.py).
_LIBPQ_ONLY_PARAMS = {"sslmode", "channel_binding"}


def _resolve_env_file() -> str | None:
    env_path = Path(__file__).resolve().parent.parent / ".env"
    return str(env_path) if env_path.is_file() else None


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ENVIRONMENT: str = "production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    CORS_ORIGINS: str = "http://localhost:3000"
    UPLOADS_DIR: str = "uploads"

    model_config = SettingsConfigDict(
        env_file=_resolve_env_file(),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        if not isinstance(value, str):
            return value
        url = value.strip()
        if url.startswith("postgres://"):
            url = "postgresql+asyncpg://" + url[len("postgres://") :]
        elif url.startswith("postgresql://") and "+asyncpg" not in url:
            url = "postgresql+asyncpg://" + url[len("postgresql://") :]

        parts = urlsplit(url)
        cleaned_query = urlencode(
            [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True)
             if k not in _LIBPQ_ONLY_PARAMS]
        )
        return urlunsplit(parts._replace(query=cleaned_query))

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


settings = Settings()
