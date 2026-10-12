import time
import uuid
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


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

    # 2. Acquisition Orchestration or Run Lookup
    if request.run_id:
        existing_run = pipeline_service.get_run(request.run_id)
        if not existing_run:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Collection run ID '{request.run_id}' not found.",
            )
        if existing_run.target.normalized_username != username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Collection run ID '{request.run_id}' belongs to target '{existing_run.target.normalized_username}', not requested '{username}'.",
            )
        unified_run = existing_run
    else:
        collection_result = await default_orchestrator.execute_collection(target=target)
        unified_run = pipeline_service.process_acquisition_result(collection_result)

    # 3. Feature Extraction & Provenance Tracking
    feature_result = extract_features_from_observations(
        username=username,
        observations=unified_run.canonical_observations,
    )

    # Enforce minimum feature coverage policy (minimum 50% or at least basic count signals to prevent ungrounded inferences)
    if not unified_run.canonical_observations or feature_result.coverage_ratio < 0.50:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Insufficient observation coverage ({feature_result.coverage_ratio * 100:.1f}%). Missing core signals: {', '.join(feature_result.missing_features)}.",
        )


    # 5. ML Model Inference & Local Attribution
    elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
    assessment = model_service.predict(
        request_id=request_id,
        username=username,
        feature_result=feature_result,
        processing_time_ms=elapsed_ms,
    )

    # 6. Durable Persistence of Assessment and Explanation
    try:
        from app.db.session import SessionLocal
        from app.db.repositories import AssessmentRepository
        with SessionLocal() as db:
            AssessmentRepository.save_assessment(db, assessment, run_id=unified_run.run_id)
    except Exception as e:
        logger.warning(f"Could not persist assessment to database: {e}")
        assessment.warnings.append(
            f"Persistence warning: Assessment computed successfully but could not be durably saved ({type(e).__name__})."
        )

    return PredictResponse(
        success=True,
        data=assessment,
    )


@router.get(
    "/{request_id}",
    response_model=PredictResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve a previously persisted prediction assessment by request_id",
)
async def get_assessment_by_id(request_id: str) -> PredictResponse:
    from app.db.session import SessionLocal
    from app.db.repositories import AssessmentRepository
    from app.schemas.prediction import ExplanationResult, FeatureContribution, KeyFactor, EvidenceItem

    with SessionLocal() as db:
        record = AssessmentRepository.get_assessment(db, request_id)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Assessment with request_id '{request_id}' not found.",
            )

        expl = record.explanation
        explanation_obj = ExplanationResult(
            status=expl.status if expl else "unavailable",
            provider=expl.provider if expl else "unavailable",
            model_id=expl.model if expl else "unknown",
            method=expl.model if expl else "unknown",
            summary=expl.summary if expl else "",
            key_factors=[KeyFactor(**f) for f in (expl.key_factors or [])] if expl else [],
            conflicting_signals=expl.conflicting_signals or [] if expl else [],
            limitations=expl.limitations or [] if expl else [],
            review_guidance=expl.review_guidance or [] if expl else [],
            contributions=[FeatureContribution(**c) for c in (expl.raw_contributions or [])] if expl else [],
            top_drivers=[c.get("feature_name", "") for c in (expl.raw_contributions or [])[:5]] if expl else [],
            warning=expl.warning if expl else None,
        )

        assessment = PredictionAssessment(
            request_id=record.request_id,
            target_username=record.target_username,
            predicted_class=record.predicted_class,
            fake_probability=record.fake_probability,
            score_label=record.score_label,
            decision_threshold=record.decision_threshold,
            model_id=record.model_id,
            pipeline_version=record.pipeline_version,
            verification_status=record.verification_status,
            verification_note=record.verification_note,
            feature_coverage_ratio=record.feature_coverage_ratio,
            missing_features=record.missing_features or [],
            extracted_features=record.extracted_features or {},
            evidence=[EvidenceItem(**e) for e in (record.evidence or [])],
            explanation=explanation_obj,
            warnings=record.warnings or [],
            processing_time_ms=record.processing_time_ms,
            created_at=record.created_at,
        )

    return PredictResponse(
        success=True,
        data=assessment,
    )


