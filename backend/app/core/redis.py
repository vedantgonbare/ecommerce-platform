import redis.asyncio as redis
from app.core.config import settings

redis_client = redis.from_url(settings.redis_url, decode_responses=True)

async def invalidate_pattern(pattern: str) -> None:
    cursor = 0
    while True:
        cursor, keys = await redis_client.scan(cursor=cursor, match=pattern, count=100)
        if keys:
            await redis_client.delete(*keys)
        if cursor == 0:
            break