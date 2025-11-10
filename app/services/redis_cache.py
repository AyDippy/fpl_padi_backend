# app/core/cache.py
import redis.asyncio as redis
from app.core.config import settings
from app.core.logging import logger
from typing import Optional, Type

class Cache:
    """
    A robust, asynchronous Redis caching utility class.

    This class employs a singleton pattern for a shared connection pool,
    ensuring efficient connection management. It provides graceful degradation,
    allowing the application to run without caching if Redis is unavailable.

    All methods are classmethods, so no instance of this class is needed.
    Usage:
        await Cache.set("my_key", "my_value")
        value = await Cache.get("my_key")
        await Cache.close()
    """
    _client: Optional[redis.Redis] = None
    _ttl: int = settings.REDIS_SCOUT_CACHE_TTL

    @classmethod
    async def _get_client(cls) -> Optional[redis.Redis]:
        """
        Lazily initializes and returns the Redis client connection.

        If a connection already exists, it is returned. If Redis is
        unavailable, logs a warning and returns None.
        """
        if cls._client is not None:
            return cls._client

        try:
            cls._client = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            await cls._client.ping()
            logger.info("Redis cache connected and ready.")
            return cls._client
        except Exception as e:
            logger.warning(f"Redis unavailable: {e}. Caching is disabled.")
            cls._client = None  # Ensure we don't retry on subsequent calls
            return None

    @classmethod
    async def set(cls, key: str, value: str) -> bool:
        """
        Saves a key-value pair to the cache with a pre-configured TTL.

        Args:
            key: The key under which to store the value.
            value: The string value to store.

        Returns:
            True if the value was successfully set, False otherwise.
        """
        client = await cls._get_client()
        if not client:
            return False

        try:
            await client.setex(key, cls._ttl, value)
            logger.info(f"Cache SET: {key} (TTL: {cls._ttl}s)")
            return True
        except Exception as e:
            logger.error(f"Redis SET error for key '{key}': {e}")
            return False

    @classmethod
    async def get(cls, key: str) -> Optional[str]:
        """
        Retrieves a value from the cache by its key.

        Args:
            key: The key of the value to retrieve.

        Returns:
            The cached string value if found, otherwise None.
        """
        client = await cls._get_client()
        if not client:
            return None

        try:
            value = await client.get(key)
            if value is not None:
                logger.info(f"Cache HIT: {key}")
            else:
                logger.info(f"Cache MISS: {key}")
            return value
        except Exception as e:
            logger.error(f"Redis GET error for key '{key}': {e}")
            return None
        
    @classmethod
    async def delete(cls, key: str) -> bool:
        """
        Deletes a key from the cache.
        
        Args:
            key: The key to delete.
        
        Returns:
            True if the key was successfully deleted, False otherwise.
        """
        client = await cls._get_client()
        if not client:
            return False
        
        try:
            result = await client.delete(key)
            if result > 0:
                logger.info(f"Cache DELETE: {key}")
                return True
            else:
                logger.info(f"Cache DELETE attempted but key not found: {key}")
                return False
        except Exception as e:
            logger.error(f"Redis DELETE error for key '{key}': {e}")
            return False   

    @classmethod
    async def close(cls):
        """Closes the Redis connection pool during application shutdown."""
        if cls._client:
            await cls._client.close()
            cls._client = None
            logger.info("Redis connection closed.")