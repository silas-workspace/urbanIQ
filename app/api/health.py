"""
Health check endpoint for system status monitoring.

Provides comprehensive health checks including database connectivity,
system information, and service status for monitoring and diagnostics.
"""

from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.api.deps import SettingsDep
from app.database import check_database_connection


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str
    timestamp: datetime
    version: str
    environment: str
    services: dict[str, Any]


router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check(settings: SettingsDep) -> HealthResponse:
    """
    Comprehensive health check endpoint.

    Returns system status including:
    - Application health status
    - Current timestamp
    - Version information
    - Environment details
    - Database connectivity status

    Returns:
        HealthResponse: System health information

    Raises:
        HTTPException: If critical services are unavailable
    """
    # Check database connectivity
    db_healthy = check_database_connection()

    # Determine overall status
    overall_status = "ok" if db_healthy else "degraded"

    # Prepare service status
    services = {
        "database": {
            "status": "ok" if db_healthy else "error",
            "type": "sqlite" if settings.database_url.startswith("sqlite") else "other",
        },
        "configuration": {
            "status": "ok",
            "environment": settings.environment,
        },
    }

    # If database is critical and down, return 503
    if not db_healthy:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "error",
                "message": "Database connectivity check failed",
                "services": services,
            },
        )

    return HealthResponse(
        status=overall_status,
        timestamp=datetime.now(UTC),
        version=settings.app_version,
        environment=settings.environment,
        services=services,
    )
