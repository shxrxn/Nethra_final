"""
Rate Limiter Service - Protects against abuse and DoS attacks
UPDATED FOR REAL-TIME BEHAVIORAL ANALYSIS
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Optional
from collections import defaultdict, deque
import threading

logger = logging.getLogger(__name__)

class RateLimiter:
    """In-memory rate limiter for API protection"""
    
    def __init__(self):
        self.requests = defaultdict(deque)  # user_id -> deque of timestamps
        self.blocked_users = {}  # user_id -> block_until_timestamp
        self.lock = threading.RLock()
        
        # PRODUCTION RATE LIMITING RULES - REAL-TIME READY!
        self.rules = {
            "login": {"limit": 10, "window": 300},          # 10 per 5 minutes
            "behavioral": {"limit": 3600, "window": 60},    # 60 per second!
            "trust": {"limit": 1800, "window": 60},         # 30 per second
            "session": {"limit": 600, "window": 60},        # 10 per second
            "monitoring": {"limit": 1000, "window": 60},    # 16 per second
            "general": {"limit": 50000, "window": 3600}     # 50k per hour
        }
        
        # Development bypass
        self.bypass_users = {"test_user_123", "demo_user", "admin"}
    
    async def is_allowed(self, user_id: str, endpoint_type: str = "general") -> bool:
        """Check if request is allowed for user"""
        try:
            # Bypass for test users
            if user_id in self.bypass_users:
                return True
                
            with self.lock:
                current_time = time.time()
                
                # Check if user is currently blocked
                if user_id in self.blocked_users:
                    if current_time < self.blocked_users[user_id]:
                        return False
                    else:
                        # Block expired, remove it
                        del self.blocked_users[user_id]
                
                # Get rate limiting rule
                rule = self.rules.get(endpoint_type, self.rules["general"])
                limit = rule["limit"]
                window = rule["window"]
                
                # Clean old requests outside the window
                user_requests = self.requests[user_id]
                cutoff_time = current_time - window
                
                while user_requests and user_requests[0] < cutoff_time:
                    user_requests.popleft()
                
                # Check if limit exceeded
                if len(user_requests) >= limit:
                    # Block user for double the window time
                    block_duration = window * 2
                    self.blocked_users[user_id] = current_time + block_duration
                    
                    logger.warning(f"Rate limit exceeded for user {user_id} on {endpoint_type}")
                    return False
                
                # Add current request
                user_requests.append(current_time)
                return True
                
        except Exception as e:
            logger.error(f"Rate limiting check failed: {str(e)}")
            return True  # Allow on error to avoid blocking legitimate users
    
    async def record_request(self, user_id: str, endpoint_type: str = "general"):
        """Record a request (called after is_allowed returns True)"""
        # Request already recorded in is_allowed
        pass
    
    def get_stats(self) -> Dict:
        """Get rate limiting statistics"""
        try:
            with self.lock:
                current_time = time.time()
                
                stats = {
                    "active_users": len(self.requests),
                    "blocked_users": len(self.blocked_users),
                    "total_requests_last_hour": 0,
                    "current_limits": {
                        endpoint: f"{rules['limit']} per {rules['window']}s"
                        for endpoint, rules in self.rules.items()
                    },
                    "bypass_users_count": len(self.bypass_users),
                    "blocked_users_list": []
                }
                
                # Count requests in last hour
                cutoff_time = current_time - 3600
                for user_id, user_requests in self.requests.items():
                    recent_requests = [req for req in user_requests if req > cutoff_time]
                    stats["total_requests_last_hour"] += len(recent_requests)
                
                # List currently blocked users
                for user_id, block_until in self.blocked_users.items():
                    if current_time < block_until:
                        stats["blocked_users_list"].append({
                            "user_id": user_id,
                            "blocked_until": datetime.fromtimestamp(block_until).isoformat(),
                            "remaining_seconds": int(block_until - current_time)
                        })
                
                return stats
                
        except Exception as e:
            logger.error(f"Failed to get rate limiter stats: {str(e)}")
            return {}
    
    async def unblock_user(self, user_id: str) -> bool:
        """Manually unblock a user"""
        try:
            with self.lock:
                if user_id in self.blocked_users:
                    del self.blocked_users[user_id]
                    logger.info(f"Manually unblocked user {user_id}")
                    return True
                return False
                
        except Exception as e:
            logger.error(f"Failed to unblock user: {str(e)}")
            return False
    
    def cleanup_old_data(self):
        """Clean up old request data"""
        try:
            with self.lock:
                current_time = time.time()
                cutoff_time = current_time - 7200  # Keep 2 hours of data
                
                # Clean old requests
                users_to_remove = []
                for user_id, user_requests in self.requests.items():
                    while user_requests and user_requests[0] < cutoff_time:
                        user_requests.popleft()
                    
                    if not user_requests:
                        users_to_remove.append(user_id)
                
                for user_id in users_to_remove:
                    del self.requests[user_id]
                
                # Clean expired blocks
                expired_blocks = []
                for user_id, block_until in self.blocked_users.items():
                    if current_time >= block_until:
                        expired_blocks.append(user_id)
                
                for user_id in expired_blocks:
                    del self.blocked_users[user_id]
                    
        except Exception as e:
            logger.error(f"Rate limiter cleanup failed: {str(e)}")

# Global rate limiter instance
rate_limiter = RateLimiter()

# Cleanup task
async def start_rate_limiter_cleanup():
    """Start background cleanup task"""
    while True:
        try:
            rate_limiter.cleanup_old_data()
            await asyncio.sleep(300)  # Cleanup every 5 minutes
        except Exception as e:
            logger.error(f"Rate limiter cleanup task error: {str(e)}")
            await asyncio.sleep(600)  # Wait longer on error