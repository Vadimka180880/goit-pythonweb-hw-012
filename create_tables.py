import asyncio
from app.src.config.config import settings
from sqlalchemy.ext.asyncio import create_async_engine
from app.src.database.models import Base

async def create_tables():
    engine = create_async_engine(settings.async_database_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        print("✅ Таблиці створені успішно!")

asyncio.run(create_tables())