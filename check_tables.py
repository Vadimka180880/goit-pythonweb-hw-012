import asyncio
from sqlalchemy import text
from app.src.config.config import settings
from sqlalchemy.ext.asyncio import create_async_engine

async def check_tables():
    print("🔄 Підключення до:", settings.async_database_url)
    engine = create_async_engine(settings.async_database_url)
    try:
        async with engine.connect() as conn:
            # Перевірка версії PostgreSQL
            version = await conn.scalar(text("SELECT version()"))
            print("ℹ️ Версія PostgreSQL:", version.split('\n')[0])
            
            # Перевірка таблиць
            tables = await conn.scalars(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """))
            print("📊 Таблиці у базі даних:", tables.all())
    except Exception as e:
        print("❌ Помилка:", e)

asyncio.run(check_tables())

async def check_data():
    engine = create_async_engine(settings.async_database_url)
    async with engine.connect() as conn:
        users_count = await conn.scalar(text("SELECT COUNT(*) FROM users"))
        print(f"👥 Користувачів у базі: {users_count}")

asyncio.run(check_data())