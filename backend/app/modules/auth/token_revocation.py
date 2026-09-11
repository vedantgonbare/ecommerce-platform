from datetime import datetime, timezone

from app.core.redis import redis_client


def _seconds_until(expire: datetime) -> int:
    """How many seconds remain until a token's own expiry. Never negative."""
    remaining = (expire - datetime.now(timezone.utc)).total_seconds()
    return max(int(remaining), 0)


async def revoke_refresh_token(jti: str, expire: datetime) -> None:
    """Marks a refresh token's jti as revoked. The Redis key self-expires at the
    same moment the token itself would have expired naturally — no cleanup needed."""
    ttl = _seconds_until(expire)
    if ttl > 0:
        await redis_client.set(f"revoked_jti:{jti}", "1", ex=ttl)


async def is_refresh_token_revoked(jti: str) -> bool:
    return await redis_client.get(f"revoked_jti:{jti}") is not None