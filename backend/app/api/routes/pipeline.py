from typing import Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.schemas.account import (
    AccountTarget,
    sanitize_and_validate_target,
)
from app.schemas.pipeline import UnifiedCollectionRun
from app.collectors.orchestrator import default_orchestrator
from app.pipeline.service import pipeline_service

router = APIRouter(prefix="/pipeline", tags=["Unified Data Pipeline"])


class RunPipelineRequest(BaseModel):
    input: str = Field(..., min_length=1, max_length=255, description="Instagram username or profile URL")


class PipelineResponse(BaseModel):
    success: bool = True
    data: UnifiedCollectionRun


@router.post(
    "/process",
    response_model=PipelineResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute multi-adapter acquisition, normalization, deduplication, and quality assessment",
)
async def process_account_pipeline(request: RunPipelineRequest) -> PipelineResponse:
    try:
        username, canonical_url, input_type = sanitize_and_validate_target(request.input)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )

    target = AccountTarget(
        original_input=request.input,
        normalized_username=username,
        canonical_profile_url=canonical_url,
        input_type=input_type,
    )

    # 1. Execute acquisition
    collection_result = await default_orchestrator.execute_collection(target=target)

    # 2. Run normalization, deduplication, and quality pipeline
    unified_run = pipeline_service.process_acquisition_result(collection_result)

    return PipelineResponse(
        success=True,
        data=unified_run,
    )
