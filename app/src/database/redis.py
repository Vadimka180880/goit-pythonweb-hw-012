from redis import asyncio as redis
from app.src.config.config import settings

async def get_redis():
    redis_connection = await redis.Redis.from_url(
        settings.REDIS_URL,
        decode_responses=True
    )
    try:
        yield redis_connection
    finally:
        await redis_connection.close()