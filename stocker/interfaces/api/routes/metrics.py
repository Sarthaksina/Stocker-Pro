"""Metrics endpoints for STOCKER Pro API.

This module provides endpoints for exposing application metrics for monitoring.
"""

import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Counter as CounterType
from collections import Counter, defaultdict
import threading
import psutil
import os

from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel, Field

from stocker.core.config.settings import get_settings
from stocker.core.logging import get_logger

# Initialize logger
logger = get_logger(__name__)

# Create router
router = APIRouter(tags=["Metrics"])

# Metrics storage
class MetricsStore:
    """Thread-safe storage for application metrics."""
    
    def __init__(self):
        self._lock = threading.RLock()
        self.requests_total: CounterType[str] = Counter()
        self.requests_by_path: CounterType[str] = Counter()
        self.requests_by_method: CounterType[str] = Counter()
        self.errors_total: CounterType[str] = Counter()
        self.errors_by_path: CounterType[str] = Counter()
        self.errors_by_status: CounterType[int] = Counter()
        self.response_times: defaultdict[str, List[float]] = defaultdict(list)
        self.start_time = time.time()
    
    def track_request(self, path: str, method: str) -> None:
        """Track a new request.
        
        Args:
            path: Request path
            method: HTTP method
        """
        with self._lock:
            self.requests_total["count"] += 1
            self.requests_by_path[path] += 1
            self.requests_by_method[method] += 1
    
    def track_error(self, path: str, status_code: int) -> None:
        """Track an error response.
        
        Args:
            path: Request path
            status_code: HTTP status code
        """
        with self._lock:
            self.errors_total["count"] += 1
            self.errors_by_path[path] += 1
            self.errors_by_status[status_code] += 1
    
    def track_response_time(self, path: str, duration_ms: float) -> None:
        """Track response time for a path.
        
        Args:
            path: Request path
            duration_ms: Response time in milliseconds
        """
        with self._lock:
            # Keep only the last 1000 response times per path to limit memory usage
            times = self.response_times[path]
            times.append(duration_ms)
            if len(times) > 1000:
                self.response_times[path] = times[-1000:]
    
    def get_response_time_stats(self, path: str) -> Dict[str, float]:
        """Get response time statistics for a path.
        
        Args:
            path: Request path
            
        Returns:
            Dict[str, float]: Response time statistics
        """
        with self._lock:
            times = self.response_times.get(path, [])
            if not times:
                return {"min": 0, "max": 0, "avg": 0, "p95": 0, "p99": 0, "count": 0}
            
            times_sorted = sorted(times)
            p95_idx = int(len(times) * 0.95)
            p99_idx = int(len(times) * 0.99)
            
            return {
                "min": min(times),
                "max": max(times),
                "avg": sum(times) / len(times),
                "p95": times_sorted[p95_idx - 1] if p95_idx > 0 else times_sorted[0],
                "p99": times_sorted[p99_idx - 1] if p99_idx > 0 else times_sorted[0],
                "count": len(times)
            }
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all metrics.
        
        Returns:
            Dict[str, Any]: All metrics
        """
        with self._lock:
            # Get system metrics
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            cpu_percent = process.cpu_percent(interval=0.1)
            
            # Calculate uptime
            uptime_seconds = time.time() - self.start_time
            
            # Calculate request rate (requests per second)
            request_rate = self.requests_total["count"] / max(1, uptime_seconds)
            
            # Calculate error rate
            error_rate = 0
            if self.requests_total["count"] > 0:
                error_rate = self.errors_total["count"] / self.requests_total["count"]
            
            # Get response time stats for top paths
            response_time_stats = {}
            for path in self.requests_by_path:
                response_time_stats[path] = self.get_response_time_stats(path)
            
            return {
                "requests": {
                    "total": dict(self.requests_total),
                    "by_path": dict(self.requests_by_path),
                    "by_method": dict(self.requests_by_method),
                    "rate": request_rate
                },
                "errors": {
                    "total": dict(self.errors_total),
                    "by_path": dict(self.errors_by_path),
                    "by_status": {str(k): v for k, v in self.errors_by_status.items()},
                    "rate": error_rate
                },
                "response_times": response_time_stats,
                "system": {
                    "memory": {
                        "rss": memory_info.rss,
                        "rss_mb": memory_info.rss / (1024 * 1024),
                        "vms": memory_info.vms,
                        "vms_mb": memory_info.vms / (1024 * 1024)
                    },
                    "cpu": {
                        "percent": cpu_percent
                    },
                    "uptime": {
                        "seconds": uptime_seconds,
                        "minutes": uptime_seconds / 60,
                        "hours": uptime_seconds / 3600
                    }
                }
            }


# Create metrics store singleton
metrics_store = MetricsStore()


class PrometheusMetricsResponse(Response):
    """Custom response for Prometheus metrics."""
    media_type = "text/plain"


def get_prometheus_metrics() -> str:
    """Convert metrics to Prometheus format.
    
    Returns:
        str: Metrics in Prometheus format
    """
    metrics = metrics_store.get_all_metrics()
    lines = []
    
    # Requests total
    lines.append("# HELP stocker_requests_total Total number of requests")
    lines.append("# TYPE stocker_requests_total counter")
    lines.append(f"stocker_requests_total {metrics['requests']['total'].get('count', 0)}")
    
    # Requests by path
    lines.append("# HELP stocker_requests_by_path Requests by path")
    lines.append("# TYPE stocker_requests_by_path counter")
    for path, count in metrics['requests']['by_path'].items():
        # Sanitize path for Prometheus
        path_label = path.replace('"', '').replace('\'', '')
        lines.append(f'stocker_requests_by_path{{path="{path_label}"}} {count}')
    
    # Requests by method
    lines.append("# HELP stocker_requests_by_method Requests by HTTP method")
    lines.append("# TYPE stocker_requests_by_method counter")
    for method, count in metrics['requests']['by_method'].items():
        lines.append(f'stocker_requests_by_method{{method="{method}"}} {count}')
    
    # Request rate
    lines.append("# HELP stocker_request_rate Requests per second")
    lines.append("# TYPE stocker_request_rate gauge")
    lines.append(f"stocker_request_rate {metrics['requests']['rate']:.2f}")
    
    # Errors total
    lines.append("# HELP stocker_errors_total Total number of errors")
    lines.append("# TYPE stocker_errors_total counter")
    lines.append(f"stocker_errors_total {metrics['errors']['total'].get('count', 0)}")
    
    # Error rate
    lines.append("# HELP stocker_error_rate Error rate (errors/requests)")
    lines.append("# TYPE stocker_error_rate gauge")
    lines.append(f"stocker_error_rate {metrics['errors']['rate']:.4f}")
    
    # Response times
    lines.append("# HELP stocker_response_time_ms Response time in milliseconds")
    lines.append("# TYPE stocker_response_time_ms gauge")
    for path, stats in metrics['response_times'].items():
        # Sanitize path for Prometheus
        path_label = path.replace('"', '').replace('\'', '')
        for stat_name, value in stats.items():
            if stat_name != "count":
                lines.append(f'stocker_response_time_ms{{path="{path_label}", stat="{stat_name}"}} {value:.2f}')
    
    # Memory usage
    lines.append("# HELP stocker_memory_usage_bytes Memory usage in bytes")
    lines.append("# TYPE stocker_memory_usage_bytes gauge")
    lines.append(f"stocker_memory_usage_bytes{{type=\"rss\"}} {metrics['system']['memory']['rss']}")
    lines.append(f"stocker_memory_usage_bytes{{type=\"vms\"}} {metrics['system']['memory']['vms']}")
    
    # CPU usage
    lines.append("# HELP stocker_cpu_usage CPU usage percentage")
    lines.append("# TYPE stocker_cpu_usage gauge")
    lines.append(f"stocker_cpu_usage {metrics['system']['cpu']['percent']:.2f}")
    
    # Uptime
    lines.append("# HELP stocker_uptime_seconds Uptime in seconds")
    lines.append("# TYPE stocker_uptime_seconds counter")
    lines.append(f"stocker_uptime_seconds {metrics['system']['uptime']['seconds']:.1f}")
    
    return "\n".join(lines)


@router.get(
    "/metrics",
    summary="Application Metrics",
    description="Get application metrics in JSON format",
    response_model_exclude_none=True
)
async def get_metrics() -> Dict[str, Any]:
    """Get application metrics in JSON format.
    
    Returns:
        Dict[str, Any]: Application metrics
    """
    return metrics_store.get_all_metrics()


@router.get(
    "/metrics/prometheus",
    summary="Prometheus Metrics",
    description="Get application metrics in Prometheus format",
    response_class=PrometheusMetricsResponse
)
async def get_prometheus_metrics_endpoint() -> str:
    """Get application metrics in Prometheus format.
    
    Returns:
        str: Metrics in Prometheus format
    """
    return get_prometheus_metrics()


class RequestTimingMiddleware:
    """Middleware for tracking request timing and metrics."""
    
    def __init__(self, app):
        """Initialize middleware.
        
        Args:
            app: ASGI application
        """
        self.app = app
    
    async def __call__(self, scope, receive, send):
        """Process the request.
        
        Args:
            scope: ASGI scope
            receive: ASGI receive function
            send: ASGI send function
        """
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        
        # Get request details
        path = scope["path"]
        method = scope["method"]
        
        # Track request
        metrics_store.track_request(path, method)
        
        # Start timer
        start_time = time.time()
        
        # Create a new send function to intercept the response
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                # Get status code
                status_code = message["status"]
                
                # Track error if status code >= 400
                if status_code >= 400:
                    metrics_store.track_error(path, status_code)
                
                # Calculate response time
                duration_ms = (time.time() - start_time) * 1000
                metrics_store.track_response_time(path, duration_ms)
            
            # Pass through to original send function
            await send(message)
        
        # Process request with modified send function
        await self.app(scope, receive, send_wrapper)


def add_metrics_middleware(app) -> None:
    """Add metrics middleware to the application.
    
    Args:
        app: FastAPI application
    """
    app.add_middleware(RequestTimingMiddleware)
    logger.info("Metrics middleware added")
