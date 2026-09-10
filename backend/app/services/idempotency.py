import json
import logging
from typing import Any, Dict, Optional, Tuple
from app.core.errors import IdempotencyConflictError
from app.core.redis import redis_client

logger = logging.getLogger("cartify.idempotency")

class IdempotencyService:
    """
    Manages request idempotency using Redis atomic SET NX.
    Guarantees exactly-once processing for high-concurrency checkout and payment requests.
    """
    LOCK_TTL = 120        # Lock timeout for in-flight requests (seconds)
    RESULT_TTL = 86400    # Result cache timeout (24 hours)

    @classmethod
    async def acquire_lock(cls, key: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Attempts to acquire an idempotency lock for key.
        Returns:
            (acquired: True, None) if lock was acquired.
            (acquired: False, cached_response) if request was already processed.
        Raises:
            IdempotencyConflictError if request is currently being processed by another worker.
        """
        redis_key = f"idempotency:{key}"
        
        # Try to set lock with NX (Not Exists)
        acquired = bool(await redis_client.set(
            redis_key,
            json.dumps({"status": "PROCESSING"}),
            nx=True,
            ex=cls.LOCK_TTL,
        ))

        if acquired:
            return True, None

        # Lock was not acquired; check current state
        existing = await redis_client.get(redis_key)
        if existing:
            data = json.loads(existing)
            if data.get("status") == "COMPLETED":
                # Return cached response to the client
                return False, data.get("response")
            elif data.get("status") == "PROCESSING":
                raise IdempotencyConflictError(key)

        # In case key expired between check, retry lock acquisition once
        retry_acquired = bool(await redis_client.set(
            redis_key,
            json.dumps({"status": "PROCESSING"}),
            nx=True,
            ex=cls.LOCK_TTL,
        ))
        if retry_acquired:
            return True, None
        raise IdempotencyConflictError(key)

    @classmethod
    async def save_result(cls, key: str, status_code: int, response_data: Any) -> None:
        """
        Persists the completed response so identical retried requests return the exact same response.
        """
        redis_key = f"idempotency:{key}"
        payload = {
            "status": "COMPLETED",
            "status_code": status_code,
            "response": response_data,
        }
        await redis_client.set(redis_key, json.dumps(payload, default=str), ex=cls.RESULT_TTL)

    @classmethod
    async def release_lock(cls, key: str) -> None:
        """
        Releases the lock on failure so the client can immediately retry the request.
        """
        redis_key = f"idempotency:{key}"
        try:
            existing = await redis_client.get(redis_key)
            if existing:
                data = json.loads(existing)
                if data.get("status") == "PROCESSING":
                    await redis_client.delete(redis_key)
        except Exception as e:
            logger.warning(f"Failed to release idempotency lock for key {key}: {e}")
