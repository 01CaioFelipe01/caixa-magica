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
        _engine = create_async_engine(
            settings.DATABASE_URL,
            poolclass=NullPool,
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
