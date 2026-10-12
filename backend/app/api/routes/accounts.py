from fastapi import APIRouter, HTTPException, status
from app.schemas.account import (
    AccountTargetValidateRequest,
    AccountValidateResponse,
    AccountValidateResponseData,
    AccountTarget,
    sanitize_and_validate_target,
)

router = APIRouter(prefix="/accounts", tags=["Account Validation"])


@router.post(
    "/validate",
    response_model=AccountValidateResponse,
    status_code=status.HTTP_200_OK,
    summary="Validate and canonicalize Instagram username or URL",
    description="Validates target syntax and normalizes to canonical username and URL format without querying external services.",
)
async def validate_account(request: AccountTargetValidateRequest) -> AccountValidateResponse:
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

    return AccountValidateResponse(
        success=True,
        data=AccountValidateResponseData(
            is_valid=True,
            target=target,
            message="Target is syntactically valid and ready for investigation.",
        ),
    )
