"""
Database configuration and session management for SQLAlchemy async engine.
Provides async session dependency for FastAPI routes and repositories.
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.src.config.config import settings  

engine = create_async_engine(settings.effective_async_database_url, echo=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db():
    """
    Dependency that provides a SQLAlchemy async session for database operations.
    
    Yields:
        AsyncSession: An active database session.
    """
    async with async_session() as session:
        yield session