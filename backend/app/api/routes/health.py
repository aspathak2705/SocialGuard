from datetime import datetime, timezone
from typing import Dict, Any
from fastapi import APIRouter
from pydantic import BaseModel, Field
from app.core.config import settings

router = APIRouter(tags=["Health & Status"])


class HealthResponse(BaseModel):
    app_name: str
    api_version: str
    status: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ReadinessResponse(BaseModel):
    status: str
    ready: bool
    phase: str
    subsystems: Dict[str, str]
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


@router.get("/health", response_model=HealthResponse)
async def get_health() -> HealthResponse:
    """Basic health check verifying the FastAPI service is active."""
    return HealthResponse(
        app_name=settings.APP_NAME,
        api_version="1.0.0",
        status="healthy",
    )


@router.get("/ready", response_model=ReadinessResponse)
async def get_readiness() -> ReadinessResponse:
    """
    Readiness probe indicating application status.
    Reports Phase 2 multi-source collectors initialized and ready.
    """
    return ReadinessResponse(
        status="ready",
        ready=True,
        phase="Phase 2: Modular Data Acquisition & Orchestration",
        subsystems={
            "api_foundation": "ready",
            "account_validation": "ready",
            "collectors": "ready_phase_2",
            "orchestrator": "ready_phase_2",
            "feature_pipeline": "planned_phase_3",
            "ml_inference": "planned_phase_4",
            "database": "uninitialized_stateless",
        },
    )
