import logging
import time
from typing import Optional, Dict
import redis.asyncio as aioredis
from app.core.config import settings

logger = logging.getLogger(__name__)

redis_pool: Optional[aioredis.ConnectionPool] = None
_redis_available: Optional[bool] = None
_memory_cache: Dict[str, float] = {}  # key -> expiry timestamp


def _clean_memory_cache():
    """Removes expired entries from in-memory fallback cache."""
    now = time.time()
    expired = [k for k, exp in _memory_cache.items() if exp <= now]
    for k in expired:
        _memory_cache.pop(k, None)


def get_redis_client() -> aioredis.Redis:
    global redis_pool
    if redis_pool is None:
        redis_pool = aioredis.ConnectionPool.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            max_connections=50,
            socket_connect_timeout=0.2,
            socket_timeout=0.2
        )
    return aioredis.Redis(connection_pool=redis_pool)


async def is_update_processed(update_id: int) -> bool:
    """Checks if Telegram update_id was already processed recently (idempotency)."""
    global _redis_available
    key = f"update:processed:{update_id}"
    now = time.time()

    if _redis_available is not False:
        try:
            r = get_redis_client()
            is_new = await r.set(key, "1", nx=True, ex=86400)
            _redis_available = True
            return is_new is None
        except Exception:
            _redis_available = False

    # In-memory fallback
    _clean_memory_cache()
    if key in _memory_cache and _memory_cache[key] > now:
        return True
    _memory_cache[key] = now + 86400
    return False


async def is_notification_sent(business_conn_id: str, chat_id: int, message_id: int, event_type: str) -> bool:
    """Checks and marks notification key to prevent duplicate user notifications."""
    global _redis_available
    key = f"notify:{business_conn_id}:{chat_id}:{message_id}:{event_type}"
    now = time.time()

    if _redis_available is not False:
        try:
            r = get_redis_client()
            is_new = await r.set(key, "1", nx=True, ex=86400)
            _redis_available = True
            return is_new is None
        except Exception:
            _redis_available = False

    # In-memory fallback
    _clean_memory_cache()
    if key in _memory_cache and _memory_cache[key] > now:
        return True
    _memory_cache[key] = now + 86400
    return False


async def push_media_queue(payload: dict) -> None:
    """Pushes media download task to the Redis worker queue if available."""
    global _redis_available
    if _redis_available is not False:
        try:
            import json
            r = get_redis_client()
            await r.lpush("queue:media_downloads", json.dumps(payload))
            _redis_available = True
        except Exception:
            _redis_available = False


async def close_redis() -> None:
    global redis_pool
    if redis_pool:
        try:
            await redis_pool.disconnect()
        except Exception:
            pass
        redis_pool = None
