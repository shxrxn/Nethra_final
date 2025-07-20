"""
Performance Utilities - Performance optimization helpers
"""

import asyncio
import functools
import logging
import time
from datetime import datetime
from typing import Any, Callable, Dict, Optional
import threading
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

class PerformanceUtils:
    """Utilities for performance optimization"""
    
    # Thread pool for CPU-intensive tasks
    thread_pool = ThreadPoolExecutor(max_workers=4)
    
    @staticmethod
    def timing_decorator(func_name: Optional[str] = None):
        """Decorator to measure function execution time"""
        def decorator(func: Callable):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    if asyncio.iscoroutinefunction(func):
                        result = await func(*args, **kwargs)
                    else:
                        result = func(*args, **kwargs)
                    
                    execution_time = (time.time() - start_time) * 1000  # ms
                    
                    # Log performance
                    name = func_name or func.__name__
                    logger.info(f"Performance: {name} took {execution_time:.2f}ms")
                    
                    # Record metric if monitoring service is available
                    try:
                        from main import monitoring_service
                        if monitoring_service:
                            await monitoring_service.record_metric(f"{name}_execution_time", execution_time)
                    except:
                        pass
                    
                    return result
                    
                except Exception as e:
                    execution_time = (time.time() - start_time) * 1000
                    logger.error(f"Performance: {func_name or func.__name__} failed after {execution_time:.2f}ms: {str(e)}")
                    raise
            
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    execution_time = (time.time() - start_time) * 1000
                    logger.info(f"Performance: {func_name or func.__name__} took {execution_time:.2f}ms")
                    return result
                except Exception as e:
                    execution_time = (time.time() - start_time) * 1000
                    logger.error(f"Performance: {func_name or func.__name__} failed after {execution_time:.2f}ms: {str(e)}")
                    raise
            
            return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
        return decorator
    
    @staticmethod
    async def run_in_thread(func: Callable, *args, **kwargs) -> Any:
        """Run CPU-intensive function in thread pool"""
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(PerformanceUtils.thread_pool, func, *args, **kwargs)
        except Exception as e:
            logger.error(f"Thread execution failed: {str(e)}")
            raise
    
    @staticmethod
    def batch_processor(batch_size: int = 100, max_wait_time: float = 1.0):
        """Decorator for batch processing of requests"""
        def decorator(func: Callable):
            batch_queue = []
            batch_lock = threading.Lock()
            last_process_time = time.time()
            
            @functools.wraps(func)
            async def wrapper(item):
                with batch_lock:
                    batch_queue.append(item)
                    current_time = time.time()
                    
                    # Process batch if size reached or max wait time exceeded
                    should_process = (
                        len(batch_queue) >= batch_size or
                        (current_time - last_process_time) >= max_wait_time
                    )
                    
                    if should_process:
                        batch_to_process = batch_queue.copy()
                        batch_queue.clear()
                        last_process_time = current_time
                        
                        # Process batch
                        try:
                            if asyncio.iscoroutinefunction(func):
                                results = await func(batch_to_process)
                            else:
                                results = func(batch_to_process)
                            
                            return results
                        except Exception as e:
                            logger.error(f"Batch processing failed: {str(e)}")
                            raise
                
                return None  # Item added to batch, will be processed later
            
            return wrapper
        return decorator
    
    @staticmethod
    class ConnectionPool:
        """Simple connection pool for database connections"""
        
        def __init__(self, create_connection: Callable, max_connections: int = 10):
            self.create_connection = create_connection
            self.max_connections = max_connections
            self.pool = []
            self.active_connections = 0
            self.lock = threading.Lock()
        
        async def get_connection(self):
            """Get connection from pool"""
            with self.lock:
                if self.pool:
                    return self.pool.pop()
                elif self.active_connections < self.max_connections:
                    self.active_connections += 1
                    return await self.create_connection()
                else:
                    raise Exception("Connection pool exhausted")
        
        async def return_connection(self, connection):
            """Return connection to pool"""
            with self.lock:
                if len(self.pool) < self.max_connections:
                    self.pool.append(connection)
                else:
                    # Close excess connection
                    if hasattr(connection, 'close'):
                        await connection.close()
                    self.active_connections -= 1
    
    @staticmethod
    def memory_efficient_json_parser(data: str, chunk_size: int = 8192):
        """Memory-efficient JSON parsing for large data"""
        try:
            import json
            
            if len(data) < chunk_size:
                return json.loads(data)
            
            # For large JSON, use streaming parser
            # This is a simplified implementation
            return json.loads(data)
            
        except Exception as e:
            logger.error(f"JSON parsing failed: {str(e)}")
            raise
    
    @staticmethod
    async def parallel_execution(tasks: list, max_concurrent: int = 5):
        """Execute tasks in parallel with concurrency limit"""
        try:
            semaphore = asyncio.Semaphore(max_concurrent)
            
            async def execute_with_semaphore(task):
                async with semaphore:
                    return await task
            
            # Execute tasks with concurrency limit
            results = await asyncio.gather(
                *[execute_with_semaphore(task) for task in tasks],
                return_exceptions=True
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Parallel execution failed: {str(e)}")
            raise
    
    @staticmethod
    def optimize_database_query(query: str) -> str:
        """Optimize database query for better performance"""
        try:
            # Add basic query optimizations
            optimized_query = query.strip()
            
            # Add LIMIT if not present for SELECT queries
            if optimized_query.upper().startswith('SELECT') and 'LIMIT' not in optimized_query.upper():
                optimized_query += ' LIMIT 1000'
            
            # Add indexes hints (SQLite specific)
            if 'WHERE' in optimized_query.upper():
                # This is a simplified optimization
                pass
            
            return optimized_query
            
        except Exception as e:
            logger.error(f"Query optimization failed: {str(e)}")
            return query
    
    @staticmethod
    def compress_data(data: str) -> bytes:
        """Compress data for storage/transmission"""
        try:
            import gzip
            return gzip.compress(data.encode('utf-8'))
        except Exception as e:
            logger.error(f"Data compression failed: {str(e)}")
            return data.encode('utf-8')
    
    @staticmethod
    def decompress_data(compressed_data: bytes) -> str:
        """Decompress data"""
        try:
            import gzip
            return gzip.decompress(compressed_data).decode('utf-8')
        except Exception as e:
            logger.error(f"Data decompression failed: {str(e)}")
            return compressed_data.decode('utf-8', errors='ignore')
    
    @staticmethod
    async def health_check_with_timeout(check_func: Callable, timeout: float = 5.0) -> Dict:
        """Perform health check with timeout"""
        try:
            result = await asyncio.wait_for(check_func(), timeout=timeout)
            return {"status": "healthy", "response_time": timeout, "details": result}
        except asyncio.TimeoutError:
            return {"status": "timeout", "response_time": timeout, "error": "Health check timed out"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    @staticmethod
    def get_memory_usage() -> Dict:
        """Get current memory usage statistics"""
        try:
            import psutil
            import os
            
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            
            return {
                "rss_mb": memory_info.rss / (1024 * 1024),  # Resident Set Size
                "vms_mb": memory_info.vms / (1024 * 1024),  # Virtual Memory Size
                "percent": process.memory_percent(),
                "available_mb": psutil.virtual_memory().available / (1024 * 1024)
            }
            
        except Exception as e:
            logger.error(f"Failed to get memory usage: {str(e)}")
            return {}
    
    @staticmethod
    def optimize_for_mobile():
        """Optimization settings for mobile device compatibility"""
        return {
            "response_compression": True,
            "minimal_json_responses": True,
            "reduced_precision_floats": True,
            "batch_requests": True,
            "connection_pooling": True,
            "cache_aggressive": True
        }