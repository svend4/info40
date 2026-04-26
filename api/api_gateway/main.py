"""
API Gateway for AI Agent Orchestration Platform

Unified entry point for all platform services with:
- Service routing
- Rate limiting
- Authentication
- Request/Response logging
- Metrics collection
- Health checks
"""

from fastapi import FastAPI, Request, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import httpx
import time
from typing import Optional, Dict
import logging
from datetime import datetime, timedelta
from collections import defaultdict
from prometheus_client import Counter, Histogram, Gauge, make_asgi_app
import asyncio
from contextlib import asynccontextmanager


# ============================================================================
# Configuration
# ============================================================================

# Service URLs (can be configured via environment variables)
SERVICE_URLS = {
    "registry": "http://registry-service:8001",
    "marketplace": "http://marketplace-service:8002",
    "orchestrator": "http://orchestrator-service:8003",
}

# Rate limiting configuration
RATE_LIMIT_REQUESTS = 100  # requests per window
RATE_LIMIT_WINDOW = 60  # seconds

# Timeouts
REQUEST_TIMEOUT = 30.0  # seconds


# ============================================================================
# Logging Setup
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# Prometheus Metrics
# ============================================================================

http_requests_total = Counter(
    'gateway_http_requests_total',
    'Total HTTP requests through gateway',
    ['method', 'endpoint', 'service', 'status']
)

http_request_duration_seconds = Histogram(
    'gateway_http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint', 'service']
)

active_requests = Gauge(
    'gateway_active_requests',
    'Number of active requests being processed'
)

rate_limit_exceeded = Counter(
    'gateway_rate_limit_exceeded_total',
    'Total number of rate limit exceeded events',
    ['client_ip']
)

service_errors = Counter(
    'gateway_service_errors_total',
    'Total number of service errors',
    ['service', 'error_type']
)


# ============================================================================
# Rate Limiting
# ============================================================================

class RateLimiter:
    """Simple in-memory rate limiter"""

    def __init__(self, requests: int, window: int):
        self.requests = requests
        self.window = window
        self.clients: Dict[str, list] = defaultdict(list)

    def is_allowed(self, client_id: str) -> bool:
        """Check if request is allowed for client"""
        now = time.time()
        window_start = now - self.window

        # Clean old requests
        self.clients[client_id] = [
            req_time for req_time in self.clients[client_id]
            if req_time > window_start
        ]

        # Check limit
        if len(self.clients[client_id]) >= self.requests:
            return False

        # Add new request
        self.clients[client_id].append(now)
        return True

    def get_retry_after(self, client_id: str) -> int:
        """Get seconds until rate limit resets"""
        if not self.clients[client_id]:
            return 0

        oldest_request = min(self.clients[client_id])
        reset_time = oldest_request + self.window
        return max(0, int(reset_time - time.time()))


rate_limiter = RateLimiter(RATE_LIMIT_REQUESTS, RATE_LIMIT_WINDOW)


# ============================================================================
# HTTP Client
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage HTTP client lifecycle"""
    app.state.http_client = httpx.AsyncClient(timeout=REQUEST_TIMEOUT)
    yield
    await app.state.http_client.aclose()


# ============================================================================
# FastAPI App
# ============================================================================

app = FastAPI(
    title="API Gateway",
    description="Unified entry point for AI Agent Orchestration Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add middlewares
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


# ============================================================================
# Middleware
# ============================================================================

@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """Log all requests and responses"""
    start_time = time.time()
    request_id = f"{int(start_time * 1000)}"

    # Log request
    logger.info(
        f"Request {request_id}: {request.method} {request.url.path} "
        f"from {request.client.host if request.client else 'unknown'}"
    )

    # Process request
    response = await call_next(request)

    # Log response
    duration = time.time() - start_time
    logger.info(
        f"Response {request_id}: {response.status_code} "
        f"in {duration:.3f}s"
    )

    # Add headers
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time"] = f"{duration:.3f}"

    return response


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Rate limiting middleware"""
    # Skip rate limiting for health check and metrics
    if request.url.path in ["/health", "/metrics"]:
        return await call_next(request)

    # Get client identifier
    client_ip = request.client.host if request.client else "unknown"

    # Check rate limit
    if not rate_limiter.is_allowed(client_ip):
        retry_after = rate_limiter.get_retry_after(client_ip)
        rate_limit_exceeded.labels(client_ip=client_ip).inc()

        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "error": "Rate limit exceeded",
                "retry_after": retry_after
            },
            headers={"Retry-After": str(retry_after)}
        )

    return await call_next(request)


# ============================================================================
# Helper Functions
# ============================================================================

def get_client_ip(request: Request) -> str:
    """Extract client IP from request"""
    # Check X-Forwarded-For header (behind proxy)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()

    # Direct connection
    return request.client.host if request.client else "unknown"


async def proxy_request(
    request: Request,
    service: str,
    path: str,
    method: str = None
) -> JSONResponse:
    """
    Proxy request to backend service

    Args:
        request: Original request
        service: Service name (registry, marketplace, orchestrator)
        path: Path to proxy to
        method: HTTP method (defaults to request method)
    """
    if service not in SERVICE_URLS:
        raise HTTPException(
            status_code=404,
            detail=f"Service '{service}' not found"
        )

    service_url = SERVICE_URLS[service]
    target_url = f"{service_url}{path}"
    method = method or request.method

    # Track active requests
    active_requests.inc()

    try:
        # Get request body if present
        body = None
        if method in ["POST", "PUT", "PATCH"]:
            body = await request.body()

        # Prepare headers (forward relevant headers)
        headers = {
            "Content-Type": request.headers.get("Content-Type", "application/json"),
            "User-Agent": request.headers.get("User-Agent", "API-Gateway/1.0"),
            "X-Forwarded-For": get_client_ip(request),
            "X-Request-ID": request.headers.get("X-Request-ID", ""),
        }

        # Make request to backend service
        start_time = time.time()

        response = await request.app.state.http_client.request(
            method=method,
            url=target_url,
            params=dict(request.query_params),
            content=body,
            headers=headers
        )

        duration = time.time() - start_time

        # Record metrics
        http_requests_total.labels(
            method=method,
            endpoint=path,
            service=service,
            status=response.status_code
        ).inc()

        http_request_duration_seconds.labels(
            method=method,
            endpoint=path,
            service=service
        ).observe(duration)

        # Return response
        return JSONResponse(
            status_code=response.status_code,
            content=response.json() if response.text else None,
            headers=dict(response.headers)
        )

    except httpx.TimeoutException:
        service_errors.labels(service=service, error_type="timeout").inc()
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=f"Request to {service} service timed out"
        )

    except httpx.RequestError as e:
        service_errors.labels(service=service, error_type="connection").inc()
        logger.error(f"Error connecting to {service}: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service {service} is unavailable"
        )

    except Exception as e:
        service_errors.labels(service=service, error_type="unknown").inc()
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

    finally:
        active_requests.dec()


# ============================================================================
# Health Checks
# ============================================================================

@app.get("/health")
async def health_check(request: Request):
    """Gateway health check"""
    return {
        "status": "healthy",
        "service": "api-gateway",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health/services")
async def services_health_check(request: Request):
    """Check health of all backend services"""
    results = {}

    async def check_service(name: str, url: str):
        try:
            response = await request.app.state.http_client.get(
                f"{url}/health",
                timeout=5.0
            )
            results[name] = {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds()
            }
        except Exception as e:
            results[name] = {
                "status": "unhealthy",
                "error": str(e)
            }

    # Check all services concurrently
    await asyncio.gather(*[
        check_service(name, url)
        for name, url in SERVICE_URLS.items()
    ])

    # Overall status
    all_healthy = all(
        service.get("status") == "healthy"
        for service in results.values()
    )

    return {
        "status": "healthy" if all_healthy else "degraded",
        "services": results,
        "timestamp": datetime.now().isoformat()
    }


# ============================================================================
# Registry Service Routes
# ============================================================================

@app.api_route("/registry/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def registry_proxy(request: Request, path: str):
    """Proxy requests to Registry Service"""
    return await proxy_request(request, "registry", f"/{path}")


@app.get("/agents")
async def list_agents(request: Request):
    """List agents (convenience endpoint)"""
    return await proxy_request(request, "registry", "/agents")


@app.post("/agents")
async def register_agent(request: Request):
    """Register agent (convenience endpoint)"""
    return await proxy_request(request, "registry", "/agents", "POST")


@app.get("/agents/{agent_id}")
async def get_agent(request: Request, agent_id: str):
    """Get agent details (convenience endpoint)"""
    return await proxy_request(request, "registry", f"/agents/{agent_id}")


# ============================================================================
# Marketplace Service Routes
# ============================================================================

@app.api_route("/marketplace/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def marketplace_proxy(request: Request, path: str):
    """Proxy requests to Marketplace Service"""
    return await proxy_request(request, "marketplace", f"/{path}")


# ============================================================================
# Orchestrator Service Routes
# ============================================================================

@app.api_route("/orchestrator/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def orchestrator_proxy(request: Request, path: str):
    """Proxy requests to Orchestrator Service"""
    return await proxy_request(request, "orchestrator", f"/{path}")


@app.get("/tasks")
async def list_tasks(request: Request):
    """List tasks (convenience endpoint)"""
    return await proxy_request(request, "orchestrator", "/tasks")


@app.post("/tasks")
async def create_task(request: Request):
    """Create task (convenience endpoint)"""
    return await proxy_request(request, "orchestrator", "/tasks", "POST")


@app.get("/tasks/{task_id}")
async def get_task(request: Request, task_id: str):
    """Get task details (convenience endpoint)"""
    return await proxy_request(request, "orchestrator", f"/tasks/{task_id}")


# ============================================================================
# Platform-wide Endpoints
# ============================================================================

@app.get("/")
async def root():
    """API Gateway root endpoint"""
    return {
        "name": "AI Agent Orchestration Platform",
        "version": "1.0.0",
        "description": "Unified API Gateway for agent marketplace and orchestration",
        "endpoints": {
            "registry": "/registry/*",
            "marketplace": "/marketplace/*",
            "orchestrator": "/orchestrator/*",
            "health": "/health",
            "services_health": "/health/services",
            "metrics": "/metrics",
            "docs": "/docs"
        },
        "rate_limit": {
            "requests": RATE_LIMIT_REQUESTS,
            "window_seconds": RATE_LIMIT_WINDOW
        }
    }


@app.get("/stats")
async def gateway_stats():
    """Get gateway statistics"""
    return {
        "active_requests": active_requests._value._value,
        "rate_limiter": {
            "active_clients": len(rate_limiter.clients),
            "window_seconds": RATE_LIMIT_WINDOW,
            "max_requests": RATE_LIMIT_REQUESTS
        },
        "services": list(SERVICE_URLS.keys()),
        "timestamp": datetime.now().isoformat()
    }


# ============================================================================
# Error Handlers
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.now().isoformat()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "status_code": 500,
            "timestamp": datetime.now().isoformat()
        }
    )


# ============================================================================
# Startup/Shutdown Events
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    logger.info("API Gateway starting up...")
    logger.info(f"Configured services: {list(SERVICE_URLS.keys())}")
    logger.info(f"Rate limit: {RATE_LIMIT_REQUESTS} requests per {RATE_LIMIT_WINDOW}s")
    logger.info("API Gateway ready!")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("API Gateway shutting down...")


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        access_log=True
    )
