"""
Performance monitoring endpoint for analytics.
"""
from fastapi import APIRouter
from safedrive.core.cache import get_redis_client
import redis

router = APIRouter()


@router.get("/analytics/performance")
async def analytics_performance():
    """Get analytics performance metrics."""
    client = get_redis_client()
    
    metrics = {
        "redis_available": client is not None,
        "cache_enabled": client is not None,
    }
    
    if client:
        try:
            info = client.info()
            metrics.update({
                "redis_memory_used": info.get("used_memory_human"),
                "total_keys": client.dbsize(),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": round(
                    info.get("keyspace_hits", 0) / 
                    (info.get("keyspace_hits", 0) + info.get("keyspace_misses", 1)) * 100, 
                    2
                ),
            })
        except Exception as e:
            metrics["redis_error"] = str(e)
    
    return metrics
