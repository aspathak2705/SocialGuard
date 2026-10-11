import time
import uuid
from typing import Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.schemas.account import (
    AccountTarget,
    sanitize_and_validate_target,
)
from app.schemas.prediction import PredictAccountRequest, PredictionAssessment
from app.collectors.orchestrator import default_orchestrator
from app.pipeline.service import pipeline_service
from app.ml.feature_builder import extract_features_from_observations
from app.ml.model_service import model_service

router = APIRouter(prefix="/predictions", tags=["ML Predictions & Explainability"])


class PredictResponse(BaseModel):
    success: bool = True
    data: PredictionAssessment


class ModelStatusResponse(BaseModel):
    model_id: Optional[str]
    is_ready: bool
    verification_status: str
    features_count: int
    algorithm: Optional[str]


@router.get(
    "/status",
    response_model=ModelStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current ML model readiness and verification status",
)
async def get_model_status() -> ModelStatusResponse:
    if not model_service.is_loaded:
        model_service.initialize()

    return ModelStatusResponse(
        model_id=model_service.manifest.get("model_id") if model_service.manifest else None,
        is_ready=model_service.is_ready(),
        verification_status=model_service.verification_status,
        features_count=len(model_service.manifest.get("features", [])) if model_service.manifest else 0,
        algorithm=model_service.manifest.get("algorithm") if model_service.manifest else None,
    )


@router.post(
    "/analyze",
    response_model=PredictResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute multi-signal acquisition, pipeline normalization, and explainable ML inference",
)
async def analyze_account_prediction(request: PredictAccountRequest) -> PredictResponse:
    start_time = time.perf_counter()
    request_id = f"pred-{uuid.uuid4().hex[:12]}"

    if not model_service.is_loaded:
        model_service.initialize()

    if not model_service.is_ready():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Inference model service is not ready: {model_service.load_error or 'Model artifact uninitialized'}",
        )

    # 1. Target Sanitization and Validation
    try:
        username, canonical_url, input_type = sanitize_and_validate_target(request.username)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )

    target = AccountTarget(
        original_input=request.username,
        normalized_username=username,
        canonical_profile_url=canonical_url,
        input_type=input_type,
    )

    # 2. Acquisition Orchestration
    collection_result = await default_orchestrator.execute_collection(target=target)

    # 3. Canonical Pipeline Normalization & Deduplication
    unified_run = pipeline_service.process_acquisition_result(collection_result)

    # 4. Feature Extraction & Provenance Tracking
    feature_result = extract_features_from_observations(
        username=username,
        observations=unified_run.canonical_observations,
    )

    # 5. ML Model Inference & Local Attribution
    elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
    assessment = model_service.predict(
        request_id=request_id,
        username=username,
        feature_result=feature_result,
        processing_time_ms=elapsed_ms,
    )

    return PredictResponse(
        success=True,
        data=assessment,
    )
