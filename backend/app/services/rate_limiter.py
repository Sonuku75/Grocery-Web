import time
import logging
from typing import Tuple
from app.core.errors import RateLimitExceededError
from app.core.redis import redis_client

logger = logging.getLogger("cartify.rate_limiter")

class SlidingWindowRateLimiter:
    """
    Sliding Window Log Rate Limiter using Redis Sorted Sets (ZSET).
    Ensures accurate rate limiting across distributed FastAPI instances.
    """
    @classmethod
    async def is_allowed(
        cls,
        identifier: str,
        limit: int = 100,
        window_seconds: int = 60,
    ) -> Tuple[bool, int, int]:
        """
        Evaluates whether a request with the given identifier is permitted within the rate limit.
        Returns:
            (allowed: bool, remaining: int, retry_after: int)
        """
        redis_key = f"ratelimit:{identifier}"
        now = time.time()
        window_start = now - window_seconds

        try:
            async with redis_client.pipeline(transaction=True) as pipe:
                # Remove timestamps older than the sliding window
                pipe.zremrangebyscore(redis_key, 0, window_start)
                # Count current valid requests
                pipe.zcard(redis_key)
                results = await pipe.execute()

            current_count = results[1]

            if current_count >= limit:
                # Find oldest entry in the window to compute exact retry_after
                oldest_entries = await redis_client.zrange(redis_key, 0, 0, withscores=True)
                if oldest_entries:
                    oldest_time = oldest_entries[0][1]
                    retry_after = max(1, int(window_seconds - (now - oldest_time)))
                else:
                    retry_after = window_seconds
                return False, 0, retry_after

            # Add current timestamp to window
            async with redis_client.pipeline(transaction=True) as pipe:
                pipe.zadd(redis_key, {str(now): now})
                pipe.expire(redis_key, window_seconds + 10)
                await pipe.execute()

            remaining = max(0, limit - (current_count + 1))
            return True, remaining, 0

        except Exception as e:
            # Fallback policy: allow request on cache failure so Redis issues don't take down the API
            logger.error(f"Rate limiter error for {identifier}: {e}")
            return True, limit, 0

    @classmethod
    async def check_and_raise(
        cls,
        identifier: str,
        limit: int = 100,
        window_seconds: int = 60,
    ) -> None:
        """
        Checks rate limit and immediately raises RateLimitExceededError if breached.
        """
        allowed, remaining, retry_after = await cls.is_allowed(
            identifier=identifier,
            limit=limit,
            window_seconds=window_seconds,
        )
        if not allowed:
            raise RateLimitExceededError(retry_after=retry_after)
