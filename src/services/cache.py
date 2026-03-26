"""Redis cache helpers used by authentication flow."""

from __future__ import annotations

import json

import redis

from src.conf.config import get_settings

settings = get_settings()
_redis_client = None


class NullCache:
    """Fallback cache implementation used when Redis is unavailable."""

    def get(self, key: str):
        """Always return `None` for cache misses."""

        return None

    def setex(self, key: str, ttl: int, value: str):
        """Ignore cache writes when Redis is not available."""

        return True

    def delete(self, key: str):
        """Ignore delete operations when Redis is not available."""

        return 0



def get_redis_client():
    """Return a lazily created Redis client or a null-cache fallback."""

    global _redis_client
    if _redis_client is None:
        try:
            _redis_client = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                db=settings.redis_db,
                password=settings.redis_password,
                decode_responses=True,
                socket_connect_timeout=1,
            )
            _redis_client.ping()
        except Exception:
            _redis_client = NullCache()
    return _redis_client



def user_cache_key(user_id: int) -> str:
    """Build a stable cache key for serialized user data."""

    return f'user:{user_id}'



def serialize_user(user) -> str:
    """Serialize the minimal user payload stored in Redis."""

    return json.dumps(
        {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'avatar_url': user.avatar_url,
            'confirmed': user.confirmed,
            'role': getattr(user.role, 'value', str(user.role)),
        }
    )
