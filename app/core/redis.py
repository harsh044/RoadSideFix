# app/core/redis.py

from redis.asyncio import Redis

from app.core.config import settings


redis_client: Redis = Redis.from_url(
    settings.redis_url,
    encoding="utf-8",
    decode_responses=True,
)


async def check_redis_connection() -> bool:
    """
    Check whether Redis is available.
    """
    try:
        return bool(await redis_client.ping())
    except Exception as e:
        print(f"Redis connection failed: {type(e).__name__}: {e}")
        return False


async def close_redis_connection() -> None:
    """
    Close the Redis connection pool.
    """
    await redis_client.aclose()