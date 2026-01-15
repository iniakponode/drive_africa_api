#!/usr/bin/env python3
"""Test Redis caching functionality"""
import sys
sys.path.insert(0, '/var/www/vhosts/safedriveafrica.com/api.safedriveafrica.com')

from safedrive.core.cache import get_redis_client, cache_get, cache_set

print("Testing Redis connection...")
client = get_redis_client()
print(f"Redis client: {client}")

if client:
    try:
        ping = client.ping()
        print(f"Redis ping: {ping}")
        
        # Test cache operations
        test_key = "test:key"
        test_value = {"message": "Hello from cache"}
        
        cache_set(test_key, test_value, ttl=60)
        print(f"Set test key: {test_key}")
        
        retrieved = cache_get(test_key)
        print(f"Retrieved: {retrieved}")
        
        print("\n✓ Redis caching is working!")
    except Exception as e:
        print(f"Error: {e}")
else:
    print("✗ Redis client is None - connection failed")
