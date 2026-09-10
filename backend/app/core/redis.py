"""
Cartify Redis Foundation & Cache-Aside Manager (Module 0)

Architectural Rules:
1. PostgreSQL is the SOLE authoritative source of truth for transactional data.
2. Critical state (inventory levels, payment states, order status) must NEVER rely on stale cache.
3. Cache Stampede Protection: A distributed mutex lock (SET NX EX) prevents the "thundering herd"
   problem when high-traffic cache keys expire.
4. Cache Key Strategy:
   - Pattern: cache:{entity}:{identifier_or_query_hash}
   - Example: cache:categories:all, cache:product:prod_123
5. TTL Strategy:
   - Catalog & Static Data: 3600 seconds (1 hour)
   - Dynamic Feeds / Deals: 300 seconds (5 minutes)
   - Short-lived OTP / Locks: 60 - 120 seconds
"""

import json
import logging
from typing import Any, Callable, Optional
import redis.asyncio as aioredis
from app.core.config import settings

logger = logging.getLogger("cartify.redis")

# Global Redis Connection Pool
redis_pool = aioredis.ConnectionPool.from_url(
    settings.REDIS_URL,
    max_connections=settings.REDIS_POOL_MAX_CONNECTIONS,
    socket_timeout=settings.REDIS_SOCKET_TIMEOUT,
    socket_connect_timeout=settings.REDIS_CONNECT_TIMEOUT,
    decode_responses=True,
)

redis_client = aioredis.Redis(connection_pool=redis_pool)

class CacheManager:
    """
    High-Performance Cache-Aside Manager with Stampede Protection.
    """

    @staticmethod
    async def get(key: str) -> Optional[Any]:
        """Fetch and deserialize JSON from cache."""
        try:
            val = await redis_client.get(key)
            if val is not None:
                return json.loads(val)
        except Exception as e:
            logger.warning(f"Redis GET failed for key {key}: {e}")
        return None

    @staticmethod
    async def set(key: str, value: Any, ttl: int = settings.CACHE_DEFAULT_TTL) -> bool:
        """Serialize and persist value to cache with TTL."""
        try:
            serialized = json.dumps(value, default=str)
            await redis_client.set(key, serialized, ex=ttl)
            return True
        except Exception as e:
            logger.warning(f"Redis SET failed for key {key}: {e}")
            return False

    @staticmethod
    async def delete(key: str) -> bool:
        """Remove key from cache."""
        try:
            await redis_client.delete(key)
            return True
        except Exception as e:
            logger.warning(f"Redis DEL failed for key {key}: {e}")
            return False

    @staticmethod
    async def delete_pattern(pattern: str) -> int:
        """Invalidate all keys matching pattern using non-blocking SCAN."""
        try:
            cursor = 0
            deleted = 0
            while True:
                cursor, keys = await redis_client.scan(cursor=cursor, match=pattern, count=100)
                if keys:
                    deleted += await redis_client.delete(*keys)
                if cursor == 0:
                    break
            return deleted
        except Exception as e:
            logger.warning(f"Redis SCAN/DEL failed for pattern {pattern}: {e}")
            return 0

    @staticmethod
    async def get_or_set(key: str, fetcher: Callable, ttl: int = settings.CACHE_DEFAULT_TTL) -> Any:
        """
        Cache-aside pattern with distributed lock stampede protection:
        Only one worker queries the database on cache miss; others wait briefly.
        """
        cached = await CacheManager.get(key)
        if cached is not None:
            return cached

        lock_key = f"lock:stampede:{key}"
        acquired = False
        try:
            acquired = bool(await redis_client.set(lock_key, "1", nx=True, ex=5))
        except Exception:
            pass

        if acquired:
            try:
                data = await fetcher()
                await CacheManager.set(key, data, ttl=ttl)
                return data
            finally:
                try:
                    await redis_client.delete(lock_key)
                except Exception:
                    pass
        else:
            import asyncio
            for _ in range(5):
                await asyncio.sleep(0.05)
                cached = await CacheManager.get(key)
                if cached is not None:
                    return cached
            # Fallback if compute took longer
            return await fetcher()

async def ping_redis() -> bool:
    """Lightweight health check ping for Redis bounded by 1.0s timeout."""
    import asyncio
    try:
        return bool(await asyncio.wait_for(redis_client.ping(), timeout=1.0))
    except Exception:
        return False
