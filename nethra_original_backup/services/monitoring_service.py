"""
Monitoring Service - Performance and metrics monitoring
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import defaultdict, deque
import psutil
import threading

logger = logging.getLogger(__name__)

class MonitoringService:
    """Service for monitoring system performance and metrics"""
    
    def __init__(self):
        self.metrics = defaultdict(deque)
        self.counters = defaultdict(int)
        self.alerts = []
        self.max_metric_history = 1000
        self.start_time = datetime.utcnow()
        self._loop = None
        self._monitoring_task = None
        
        # Start background monitoring
        self._start_system_monitoring()
    
    def _start_system_monitoring(self):
        """Start background system monitoring"""
        def monitor_system():
            while True:
                try:
                    # Get system metrics synchronously
                    cpu_percent = psutil.cpu_percent(interval=1)
                    memory = psutil.virtual_memory()
                    disk = psutil.disk_usage('/')
                    
                    # Store metrics synchronously (no async needed)
                    self._record_metric_sync("system_cpu_usage", cpu_percent)
                    self._record_metric_sync("system_memory_usage", memory.percent)
                    self._record_metric_sync("system_memory_available", memory.available / (1024**3))
                    self._record_metric_sync("system_disk_usage", disk.percent)
                    
                    time.sleep(30)  # Monitor every 30 seconds
                    
                except Exception as e:
                    logger.error(f"System monitoring error: {str(e)}")
                    time.sleep(60)  # Wait longer on error
        
        # Start monitoring thread
        monitor_thread = threading.Thread(target=monitor_system, daemon=True)
        monitor_thread.start()
    
    def _record_metric_sync(self, metric_name: str, value: float, tags: Dict = None):
        """Record a metric value synchronously (thread-safe)"""
        try:
            timestamp = datetime.utcnow()
            
            metric_data = {
                "timestamp": timestamp,
                "value": value,
                "tags": tags or {}
            }
            
            # Add to metrics history (thread-safe)
            self.metrics[metric_name].append(metric_data)
            
            # Keep only recent metrics
            if len(self.metrics[metric_name]) > self.max_metric_history:
                self.metrics[metric_name].popleft()
            
            # Check for alerts synchronously
            self._check_alerts_sync(metric_name, value)
            
        except Exception as e:
            logger.error(f"Failed to record metric {metric_name}: {str(e)}")
    
    def _check_alerts_sync(self, metric_name: str, value: float):
        """Check if metric value triggers any alerts (synchronous)"""
        try:
            alert_thresholds = {
                "system_cpu_usage": 80.0,
                "system_memory_usage": 85.0,
                "behavioral_analysis_time": 200.0,  # ms
                "trust_score_calculation_time": 100.0,  # ms
                "database_query_time": 50.0  # ms
            }
            
            if metric_name in alert_thresholds:
                threshold = alert_thresholds[metric_name]
                
                if value > threshold:
                    alert = {
                        "timestamp": datetime.utcnow(),
                        "metric": metric_name,
                        "value": value,
                        "threshold": threshold,
                        "severity": "HIGH" if value > threshold * 1.2 else "MEDIUM"
                    }
                    
                    self.alerts.append(alert)
                    
                    # Keep only recent alerts
                    if len(self.alerts) > 100:
                        self.alerts = self.alerts[-100:]
                    
                    logger.warning(f"Alert: {metric_name} = {value} (threshold: {threshold})")
                    
        except Exception as e:
            logger.error(f"Alert checking failed: {str(e)}")
    
    async def record_metric(self, metric_name: str, value: float, tags: Dict = None):
        """Record a metric value (async version for API calls)"""
        try:
            timestamp = datetime.utcnow()
            
            metric_data = {
                "timestamp": timestamp,
                "value": value,
                "tags": tags or {}
            }
            
            # Add to metrics history
            self.metrics[metric_name].append(metric_data)
            
            # Keep only recent metrics
            if len(self.metrics[metric_name]) > self.max_metric_history:
                self.metrics[metric_name].popleft()
            
            # Check for alerts
            await self._check_alerts(metric_name, value)
            
        except Exception as e:
            logger.error(f"Failed to record metric {metric_name}: {str(e)}")
    
    async def increment_counter(self, counter_name: str, increment: int = 1):
        """Increment a counter"""
        try:
            self.counters[counter_name] += increment
        except Exception as e:
            logger.error(f"Failed to increment counter {counter_name}: {str(e)}")
    
    async def record_error(self, error_type: str, details: str = ""):
        """Record an error occurrence"""
        try:
            await self.increment_counter(f"error_{error_type}")
            
            error_data = {
                "timestamp": datetime.utcnow(),
                "error_type": error_type,
                "details": details
            }
            
            self.metrics["errors"].append(error_data)
            
            # Keep only recent errors
            if len(self.metrics["errors"]) > 100:
                self.metrics["errors"].popleft()
                
        except Exception as e:
            logger.error(f"Failed to record error: {str(e)}")
    
    async def _check_alerts(self, metric_name: str, value: float):
        """Check if metric value triggers any alerts (async version)"""
        try:
            alert_thresholds = {
                "system_cpu_usage": 80.0,
                "system_memory_usage": 85.0,
                "behavioral_analysis_time": 200.0,  # ms
                "trust_score_calculation_time": 100.0,  # ms
                "database_query_time": 50.0  # ms
            }
            
            if metric_name in alert_thresholds:
                threshold = alert_thresholds[metric_name]
                
                if value > threshold:
                    alert = {
                        "timestamp": datetime.utcnow(),
                        "metric": metric_name,
                        "value": value,
                        "threshold": threshold,
                        "severity": "HIGH" if value > threshold * 1.2 else "MEDIUM"
                    }
                    
                    self.alerts.append(alert)
                    
                    # Keep only recent alerts
                    if len(self.alerts) > 100:
                        self.alerts = self.alerts[-100:]
                    
                    logger.warning(f"Alert: {metric_name} = {value} (threshold: {threshold})")
                    
        except Exception as e:
            logger.error(f"Alert checking failed: {str(e)}")
    
    def get_metrics_summary(self) -> Dict:
        """Get summary of all metrics"""
        try:
            summary = {}
            
            for metric_name, metric_data in self.metrics.items():
                if metric_data:
                    values = [m["value"] for m in metric_data if isinstance(m.get("value"), (int, float))]
                    
                    if values:
                        summary[metric_name] = {
                            "count": len(values),
                            "avg": sum(values) / len(values),
                            "min": min(values),
                            "max": max(values),
                            "latest": values[-1] if values else 0
                        }
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to get metrics summary: {str(e)}")
            return {}
    
    def get_counters(self) -> Dict:
        """Get all counter values"""
        return dict(self.counters)
    
    def get_alerts(self, limit: int = 50) -> List[Dict]:
        """Get recent alerts"""
        return self.alerts[-limit:] if self.alerts else []
    
    def get_system_info(self) -> Dict:
        """Get system information"""
        try:
            uptime = datetime.utcnow() - self.start_time
            
            return {
                "uptime_seconds": uptime.total_seconds(),
                "uptime_formatted": str(uptime),
                "cpu_count": psutil.cpu_count(),
                "memory_total_gb": psutil.virtual_memory().total / (1024**3),
                "disk_total_gb": psutil.disk_usage('/').total / (1024**3),
                "python_version": f"{psutil.PYTHON_VERSION}",
                "process_id": psutil.Process().pid
            }
            
        except Exception as e:
            logger.error(f"Failed to get system info: {str(e)}")
            return {}
    
    def get_performance_metrics(self) -> Dict:
        """Get performance-specific metrics"""
        try:
            metrics_summary = self.get_metrics_summary()
            
            performance_metrics = {
                "response_times": {},
                "throughput": {},
                "resource_usage": {},
                "error_rates": {}
            }
            
            # Response times
            for metric in ["behavioral_analysis_time", "trust_score_calculation_time", "database_query_time"]:
                if metric in metrics_summary:
                    performance_metrics["response_times"][metric] = metrics_summary[metric]
            
            # Resource usage
            for metric in ["system_cpu_usage", "system_memory_usage", "system_disk_usage"]:
                if metric in metrics_summary:
                    performance_metrics["resource_usage"][metric] = metrics_summary[metric]
            
            # Error rates
            total_requests = self.counters.get("total_requests", 1)
            for counter_name, count in self.counters.items():
                if counter_name.startswith("error_"):
                    error_type = counter_name.replace("error_", "")
                    performance_metrics["error_rates"][error_type] = {
                        "count": count,
                        "rate": (count / total_requests) * 100
                    }
            
            return performance_metrics
            
        except Exception as e:
            logger.error(f"Failed to get performance metrics: {str(e)}")
            return {}
    
    async def record_request(self, endpoint: str, method: str, response_time: float, status_code: int):
        """Record API request metrics"""
        try:
            await self.increment_counter("total_requests")
            await self.increment_counter(f"requests_{method.lower()}")
            await self.increment_counter(f"status_{status_code}")
            
            await self.record_metric("api_response_time", response_time, {
                "endpoint": endpoint,
                "method": method,
                "status_code": status_code
            })
            
            if status_code >= 400:
                await self.record_error(f"http_{status_code}", f"{method} {endpoint}")
                
        except Exception as e:
            logger.error(f"Failed to record request metrics: {str(e)}")
    
    def export_prometheus_metrics(self) -> str:
        """Export metrics in Prometheus format"""
        try:
            prometheus_output = []
            
            # Add counters
            for counter_name, value in self.counters.items():
                prometheus_output.append(f"nethra_{counter_name}_total {value}")
            
            # Add latest metric values
            metrics_summary = self.get_metrics_summary()
            for metric_name, data in metrics_summary.items():
                if "latest" in data:
                    prometheus_output.append(f"nethra_{metric_name} {data['latest']}")
            
            return "\n".join(prometheus_output)
            
        except Exception as e:
            logger.error(f"Failed to export Prometheus metrics: {str(e)}")
            return ""