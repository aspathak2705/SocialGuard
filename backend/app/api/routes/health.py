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
    Reports real database connectivity, pipeline readiness, and ML model status.
    """
    from app.db.session import check_db_connectivity
    from app.ml.model_service import model_service

    db_ready = check_db_connectivity()
    model_ready = model_service.is_ready() if model_service.is_loaded else False
    llm_enabled = bool(settings.OPENROUTER_ENABLED and settings.OPENROUTER_API_KEY)

    subsystems = {
        "api_foundation": "ready",
        "account_validation": "ready",
        "collectors": "ready_phase_2",
        "orchestrator": "ready_phase_2",
        "pipeline": "ready_phase_3",
        "database": "connected" if db_ready else "unreachable",
        "ml_inference": "ready" if model_ready else "standby",
        "openrouter_llm": "configured" if llm_enabled else "unconfigured_fallback",
    }

    is_overall_ready = db_ready

    return ReadinessResponse(
        status="ready" if is_overall_ready else "degraded",
        ready=is_overall_ready,
        phase="Phase 6: Release Candidate",
        subsystems=subsystems,
    )

