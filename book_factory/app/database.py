"""Database setup and session management."""
from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings

engine = create_async_engine(
    f"sqlite+aiosqlite:///{settings.database_path}",
    echo=settings.debug,
)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

Base = declarative_base()


async def get_db():
    """Yield a database session for FastAPI dependencies."""
    async with AsyncSessionLocal() as session:
        yield session


async def init_db() -> None:
    """Create database tables and enable WAL mode."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        await session.execute(text("PRAGMA journal_mode=WAL"))
        await session.commit()
