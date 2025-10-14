from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

engine = create_async_engine(
    settings.database_url,
    future=True,
    echo=settings.database_echo,
    pool_pre_ping=True
)


class Base(DeclarativeBase):
    pass


async_session = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession
)


async def init_models():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncSession:
    """Dependency для получения сессии базы данных"""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


async def close_db():
    """Закрытие соединений с базой данных"""
    await engine.dispose()
