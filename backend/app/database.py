import ssl
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from app.config import settings


class Base(DeclarativeBase):
    pass


_engine = None
_async_session_factory = None


def _get_engine():
    global _engine
    if _engine is None:
        # NullPool: em serverless (Vercel) o processo Python nao persiste entre
        # invocacoes. Manter um pool em memoria e contraproducente e esgota o
        # limite de conexoes do Postgres, ja que cada cold start abre conexoes
        # que nunca sao reaproveitadas.
        # SSL: asyncpg nao aceita sslmode na query string (sintaxe libpq), entao
        # o TLS e habilitado aqui via connect_args. O sslmode ja foi removido
        # da URL em Settings.normalize_database_url.
        ssl_context = ssl.create_default_context()
        _engine = create_async_engine(
            settings.DATABASE_URL,
            poolclass=NullPool,
            connect_args={"ssl": ssl_context},
            echo=False,
            future=True,
        )
    return _engine


def _get_session_factory():
    global _async_session_factory
    if _async_session_factory is None:
        _async_session_factory = async_sessionmaker(
            bind=_get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
        )
    return _async_session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with _get_session_factory()() as session:
        yield session
