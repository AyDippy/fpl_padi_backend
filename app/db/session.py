from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings
from app.core.logging import logger
from typing import Annotated
from fastapi import Depends


logger.info(f"Creating database engine")
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    connect_args={
        "ssl": "require",
        "statement_cache_size": 0,
    },
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    echo=False,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

Base = declarative_base()

# Database session dependency
async def get_db() -> AsyncSession:
    logger.debug("Creating database session")
    try:
        async with SessionLocal() as session:
            logger.debug("Database session created successfully")
            yield session
            logger.debug("Database session closed")
    except Exception as e:
        logger.error(f"Error with database session: {str(e)}")
        raise

# db session for fastapi application
db_session = Annotated[AsyncSession, Depends(get_db)]