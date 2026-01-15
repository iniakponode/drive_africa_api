"""
Redis cache configuration for SafeDrive Africa API.
Provides caching utilities for analytics endpoints.
"""
import hashlib
import json
import os
from typing import Optional, Any
import redis
from redis.exceptions import RedisError
import logging

logger = logging.getLogger(__name__)

# Redis connection
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

# Cache TTL (in seconds)
CACHE_TTL_SHORT = 300  # 5 minutes
CACHE_TTL_MEDIUM = 600  # 10 minutes
CACHE_TTL_LONG = 1800  # 30 minutes

# Redis client singleton
_redis_client: Optional[redis.Redis] = None


def get_redis_client() -> Optional[redis.Redis]:
    """Get Redis client singleton. Returns None if Redis unavailable."""
    global _redis_client
    
    if _redis_client is None:
        try:
            _redis_client = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                db=REDIS_DB,
                password=REDIS_PASSWORD,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2,
            )
            # Test connection
            _redis_client.ping()
            logger.info(f"Redis connected: {REDIS_HOST}:{REDIS_PORT}")
        except (RedisError, Exception) as e:
            logger.warning(f"Redis unavailable: {e}. Caching disabled.")
            _redis_client = None
    
    return _redis_client


def generate_cache_key(*args, **kwargs) -> str:
    """
    Generate a consistent cache key from arguments.
    
    Example:
        key = generate_cache_key("bad_days", cohort_ids=[uuid1, uuid2], page=1)
        # Returns: "bad_days:a3f2b1c..."
    """
    # Combine all args and kwargs into a consistent string
    key_parts = [str(arg) for arg in args]
    for k, v in sorted(kwargs.items()):
        if v is not None:
            key_parts.append(f"{k}={v}")
    
    key_string = ":".join(key_parts)
    
    # Hash for consistent length
    hash_suffix = hashlib.md5(key_string.encode()).hexdigest()[:12]
    
    # Use first arg as prefix for readability
    prefix = str(args[0]) if args else "cache"
    
    return f"{prefix}:{hash_suffix}"


def cache_get(key: str) -> Optional[Any]:
    """
    Get value from cache. Returns None if not found or Redis unavailable.
    
    Args:
        key: Cache key
        
    Returns:
        Cached value (deserialized from JSON) or None
    """
    client = get_redis_client()
    if client is None:
        return None
    
    try:
        value = client.get(key)
        if value:
            logger.debug(f"Cache HIT: {key}")
            return json.loads(value)
        logger.debug(f"Cache MISS: {key}")
        return None
    except (RedisError, json.JSONDecodeError, Exception) as e:
        logger.warning(f"Cache get error for {key}: {e}")
        return None


def cache_set(key: str, value: Any, ttl: int = CACHE_TTL_SHORT) -> bool:
    """
    Set value in cache with TTL.
    
    Args:
        key: Cache key
        value: Value to cache (will be JSON serialized)
        ttl: Time to live in seconds (default 5 minutes)
        
    Returns:
        True if successfully cached, False otherwise
    """
    client = get_redis_client()
    if client is None:
        return False
    
    try:
        serialized = json.dumps(value)
        client.setex(key, ttl, serialized)
        logger.debug(f"Cache SET: {key} (TTL: {ttl}s)")
        return True
    except (RedisError, TypeError, Exception) as e:
        logger.warning(f"Cache set error for {key}: {e}")
        return False


def cache_delete(key: str) -> bool:
    """Delete key from cache."""
    client = get_redis_client()
    if client is None:
        return False
    
    try:
        client.delete(key)
        logger.debug(f"Cache DELETE: {key}")
        return True
    except (RedisError, Exception) as e:
        logger.warning(f"Cache delete error for {key}: {e}")
        return False


def cache_invalidate_pattern(pattern: str) -> int:
    """
    Delete all keys matching pattern.
    
    Args:
        pattern: Redis key pattern (e.g., "bad_days:*")
        
    Returns:
        Number of keys deleted
    """
    client = get_redis_client()
    if client is None:
        return 0
    
    try:
        keys = client.keys(pattern)
        if keys:
            deleted = client.delete(*keys)
            logger.info(f"Cache invalidated: {deleted} keys matching '{pattern}'")
            return deleted
        return 0
    except (RedisError, Exception) as e:
        logger.warning(f"Cache invalidate error for pattern {pattern}: {e}")
        return 0
