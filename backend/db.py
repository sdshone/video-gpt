import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, async_sessionmaker
from sqlalchemy.pool import AsyncAdaptedQueuePool
from models import Base
from config import get_settings

settings = get_settings()

DATABASE_URL = f"postgresql+asyncpg://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"

# Enhanced engine configuration
engine: AsyncEngine = create_async_engine(
    DATABASE_URL,
    echo=False,
    poolclass=AsyncAdaptedQueuePool,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,  # Recycle connections after 30 minutes
    pool_pre_ping=True,  # Enable connection health checks
    connect_args={
        "command_timeout": settings.API_TIMEOUT,
        "server_settings": {
            "statement_timeout": f"{settings.API_TIMEOUT * 1000}",
            "idle_in_transaction_session_timeout": f"{settings.API_TIMEOUT * 1000}"
        }
    }
)

async_session = async_sessionmaker(bind=engine, expire_on_commit=False)

async def init_db():
    async with engine.begin() as conn:
        # Create QueryInteraction table if it doesn't exist
        # This won't drop existing tables
        await conn.run_sync(Base.metadata.create_all)

async def get_db():
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()
