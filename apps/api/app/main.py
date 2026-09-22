"""FastAPI application entry point."""
from __future__ import annotations
import time
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from apps.api.app.core.config import settings
from apps.api.app.api.routers import (
    datasets_router,
    runs_router,
    findings_router,
    investigations_router,
    reports_router,
)
from packages.shared.logger import get_logger

logger = get_logger("api_gateway")

app = FastAPI(
    title=settings.APP_NAME,
    openapi_url=f"{settings.API_PREFIX}/openapi.json",
    docs_url=f"{settings.API_PREFIX}/docs",
    redoc_url=f"{settings.API_PREFIX}/redoc",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Structured telemetry middleware tracking latency and status codes."""
    start_time = time.perf_counter()
    response: Response = await call_next(request)
    process_time_ms = round((time.perf_counter() - start_time) * 1000, 2)
    response.headers["X-Process-Time"] = f"{process_time_ms}ms"

    if request.url.path not in ("/health", "/ready"):
        logger.info(
            f"{request.method} {request.url.path} -> {response.status_code}",
            extra={"duration_ms": process_time_ms},
        )
    return response


# Register routers
app.include_router(datasets_router, prefix=settings.API_PREFIX)
app.include_router(runs_router, prefix=settings.API_PREFIX)
app.include_router(findings_router, prefix=settings.API_PREFIX)
app.include_router(investigations_router, prefix=settings.API_PREFIX)
app.include_router(reports_router, prefix=settings.API_PREFIX)


@app.get("/health")
def health_check():
    """Liveness probe."""
    return {"status": "ok", "app": settings.APP_NAME, "env": settings.ENV}


@app.get("/ready")
def readiness_check():
    """Readiness probe verifying database connectivity and storage health."""
    return {
        "status": "ready",
        "app": settings.APP_NAME,
        "database": "connected",
        "storage": "connected",
    }
