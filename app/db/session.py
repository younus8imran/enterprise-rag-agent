from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.core.config import settings
from app.core.logging import logger

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.APP_DEBUG,
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=10,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

async def get_db():
    """Dependency to get SQLAlchemy async session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            logger.error("database_session_error", error=str(e))
            raise
        finally:
            await session.close()
