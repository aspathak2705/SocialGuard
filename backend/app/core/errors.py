from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.schemas.common import ErrorResponse, ErrorDetail


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    content = ErrorResponse(
        success=False,
        error=ErrorDetail(
            code=f"HTTP_{exc.status_code}",
            message=str(exc.detail),
        )
    ).model_dump(mode="json")
    return JSONResponse(status_code=exc.status_code, content=content)


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    raw_errors = exc.errors()
    # Format errors to ensure all fields are JSON serializable
    safe_details = []
    for err in raw_errors:
        safe_err = {
            "type": err.get("type", "value_error"),
            "loc": err.get("loc", []),
            "msg": err.get("msg", "Invalid value"),
        }
        safe_details.append(safe_err)

    first_error = safe_details[0]["msg"] if safe_details else "Input validation failed."
    content = ErrorResponse(
        success=False,
        error=ErrorDetail(
            code="VALIDATION_ERROR",
            message=first_error,
            details=safe_details,
        )
    ).model_dump(mode="json")
    return JSONResponse(status_code=422, content=content)


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    content = ErrorResponse(
        success=False,
        error=ErrorDetail(
            code="INTERNAL_SERVER_ERROR",
            message="An unexpected server error occurred. Internal details suppressed.",
        )
    ).model_dump(mode="json")
    return JSONResponse(status_code=500, content=content)
