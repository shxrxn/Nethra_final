"""
Cache Service - In-memory caching for performance optimization
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Callable
import json
import hashlib
from collections import OrderedDict
import threading

logger = logging.getLogger(__name__)

class CacheService:
    """In-memory cache service with TTL and LRU eviction"""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 1800):  # Reduced size
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache = OrderedDict()
        self.expiry_times = {}
        self.hit_count = 0
        self.miss_count = 0
        self.lock = threading.RLock()
        
        # Start cleanup task
        self._start_cleanup_task()
    
    def _start_cleanup_task(self):
        """Start background task to clean expired entries"""
        def cleanup_expired():
            while True:
                try:
                    self._cleanup_expired_entries()
                    time.sleep(60)  # Cleanup every minute
                except Exception as e:
                    logger.error(f"Cache cleanup error: {str(e)}")
                    time.sleep(300)  # Wait 5 minutes on error
        
        cleanup_thread = threading.Thread(target=cleanup_expired, daemon=True)
        cleanup_thread.start()
    
    def _cleanup_expired_entries(self):
        """Remove expired entries from cache"""
        try:
            with self.lock:
                current_time = time.time()
                expired_keys = []
                
                for key, expiry_time in self.expiry_times.items():
                    if current_time > expiry_time:
                        expired_keys.append(key)
                
                for key in expired_keys:
                    self._remove_key(key)
                    
        except Exception as e:
            logger.error(f"Failed to cleanup expired entries: {str(e)}")
    
    def _remove_key(self, key: str):
        """Remove key from cache and expiry tracking"""
        try:
            if key in self.cache:
                del self.cache[key]
            if key in self.expiry_times:
                del self.expiry_times[key]
        except Exception as e:
            logger.error(f"Failed to remove key {key}: {str(e)}")
    
    def _evict_lru(self):
        """Evict least recently used item"""
        try:
            if self.cache:
                oldest_key = next(iter(self.cache))
                self._remove_key(oldest_key)
        except Exception as e:
            logger.error(f"Failed to evict LRU item: {str(e)}")
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate cache key from arguments"""
        try:
            key_data = {
                "prefix": prefix,
                "args": args,
                "kwargs": kwargs
            }
            key_string = json.dumps(key_data, sort_keys=True, default=str)
            return hashlib.md5(key_string.encode()).hexdigest()
        except Exception as e:
            logger.error(f"Failed to generate cache key: {str(e)}")
            return f"{prefix}_{hash(str(args) + str(kwargs))}"
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            with self.lock:
                current_time = time.time()
                
                # Check if key exists and not expired
                if key in self.cache:
                    if key in self.expiry_times and current_time > self.expiry_times[key]:
                        # Expired
                        self._remove_key(key)
                        self.miss_count += 1
                        return None
                    
                    # Move to end (mark as recently used)
                    value = self.cache.pop(key)
                    self.cache[key] = value
                    self.hit_count += 1
                    return value
                
                self.miss_count += 1
                return None
                
        except Exception as e:
            logger.error(f"Cache get failed for key {key}: {str(e)}")
            self.miss_count += 1
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with TTL"""
        try:
            with self.lock:
                # Use default TTL if not specified
                if ttl is None:
                    ttl = self.default_ttl
                
                # Calculate expiry time
                expiry_time = time.time() + ttl
                
                # Remove existing key if present
                if key in self.cache:
                    self._remove_key(key)
                
                # Evict if cache is full
                while len(self.cache) >= self.max_size:
                    self._evict_lru()
                
                # Add new entry
                self.cache[key] = value
                self.expiry_times[key] = expiry_time
                
                return True
                
        except Exception as e:
            logger.error(f"Cache set failed for key {key}: {str(e)}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        try:
            with self.lock:
                if key in self.cache:
                    self._remove_key(key)
                    return True
                return False
                
        except Exception as e:
            logger.error(f"Cache delete failed for key {key}: {str(e)}")
            return False
    
    async def clear(self):
        """Clear all cache entries"""
        try:
            with self.lock:
                self.cache.clear()
                self.expiry_times.clear()
                
        except Exception as e:
            logger.error(f"Cache clear failed: {str(e)}")
    
    def get_stats(self) -> Dict:
        """Get cache statistics"""
        try:
            with self.lock:
                total_requests = self.hit_count + self.miss_count
                hit_rate = (self.hit_count / total_requests * 100) if total_requests > 0 else 0
                
                return {
                    "size": len(self.cache),
                    "max_size": self.max_size,
                    "hit_count": self.hit_count,
                    "miss_count": self.miss_count,
                    "hit_rate": round(hit_rate, 2),
                    "memory_usage_mb": self._estimate_memory_usage()
                }
                
        except Exception as e:
            logger.error(f"Failed to get cache stats: {str(e)}")
            return {}
    
    def _estimate_memory_usage(self) -> float:
        """Estimate memory usage in MB"""
        try:
            import sys
            total_size = 0
            
            for key, value in self.cache.items():
                total_size += sys.getsizeof(key) + sys.getsizeof(value)
            
            return total_size / (1024 * 1024)  # Convert to MB
            
        except Exception as e:
            logger.error(f"Failed to estimate memory usage: {str(e)}")
            return 0.0
    
    # Specialized cache methods for NETHRA
    async def cache_user_baseline(self, user_id: str, baseline: Dict, ttl: int = 1800):
        """Cache user behavioral baseline"""
        key = f"user_baseline_{user_id}"
        return await self.set(key, baseline, ttl)
    
    async def get_user_baseline(self, user_id: str) -> Optional[Dict]:
        """Get cached user baseline"""
        key = f"user_baseline_{user_id}"
        return await self.get(key)
    
    async def cache_trust_score(self, session_id: str, trust_data: Dict, ttl: int = 300):
        """Cache trust score calculation"""
        key = f"trust_score_{session_id}"
        return await self.set(key, trust_data, ttl)
    
    async def get_trust_score(self, session_id: str) -> Optional[Dict]:
        """Get cached trust score"""
        key = f"trust_score_{session_id}"
        return await self.get(key)
    
    async def cache_session_data(self, session_id: str, session_data: Dict, ttl: int = 600):
        """Cache session data"""
        key = f"session_{session_id}"
        return await self.set(key, session_data, ttl)
    
    async def get_session_data(self, session_id: str) -> Optional[Dict]:
        """Get cached session data"""
        key = f"session_{session_id}"
        return await self.get(key)
    
    async def invalidate_user_cache(self, user_id: str):
        """Invalidate all cache entries for a user"""
        try:
            with self.lock:
                keys_to_delete = []
                
                for key in self.cache.keys():
                    if user_id in key:
                        keys_to_delete.append(key)
                
                for key in keys_to_delete:
                    self._remove_key(key)
                    
        except Exception as e:
            logger.error(f"Failed to invalidate user cache: {str(e)}")