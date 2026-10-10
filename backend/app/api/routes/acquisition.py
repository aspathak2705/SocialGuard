from typing import Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.schemas.account import (
    AccountTargetValidateRequest,
    AccountTarget,
    sanitize_and_validate_target,
)
from app.schemas.collection import CollectionResult
from app.collectors.orchestrator import default_orchestrator

router = APIRouter(prefix="/acquisition", tags=["Data Acquisition"])


class StartAcquisitionRequest(BaseModel):
    input: str = Field(..., min_length=1, max_length=255, description="Instagram username or profile URL")


class AcquisitionResponse(BaseModel):
    success: bool = True
    data: CollectionResult


@router.post(
    "/collect",
    response_model=AcquisitionResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute multi-adapter data acquisition for validated target",
    description="Validates target syntax and coordinates eligible collectors (Instaloader, gallery-dl, Playwright) with bounded timeouts.",
)
async def collect_account_data(request: StartAcquisitionRequest) -> AcquisitionResponse:
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

    result = await default_orchestrator.execute_collection(target=target)

    return AcquisitionResponse(
        success=True,
        data=result,
    )
