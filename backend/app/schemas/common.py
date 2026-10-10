from datetime import datetime, timezone
from typing import Any, Optional
from pydantic import BaseModel, Field


class BaseResponse(BaseModel):
    success: bool
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    data: Optional[Any] = None
    error: Optional[Any] = None


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[Any] = None


class ErrorResponse(BaseModel):
    success: bool = False
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    error: ErrorDetail
