from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from app.schemas.account import AccountTarget


class CollectorSource(str, Enum):
    INSTALOADER = "instaloader"
    GALLERY_DL = "gallery-dl"
    PLAYWRIGHT = "playwright"


class DataSourceExecutionStatus(str, Enum):
    PENDING = "pending"
    NOT_IMPLEMENTED = "not_implemented"
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    SKIPPED = "skipped"


class DataSourceStatus(BaseModel):
    source: CollectorSource
    status: DataSourceExecutionStatus = DataSourceExecutionStatus.NOT_IMPLEMENTED
    collected_field_names: List[str] = Field(default_factory=list)
    missing_field_names: List[str] = Field(default_factory=list)
    error_code: Optional[str] = None
    collection_timestamp: Optional[datetime] = None


class AccountObservation(BaseModel):
    account_id: Optional[str] = None
    username: str
    full_name: Optional[str] = None
    biography: Optional[str] = None
    is_private: Optional[bool] = None
    is_verified: Optional[bool] = None
    posts_count: Optional[int] = None
    followers_count: Optional[int] = None
    following_count: Optional[int] = None
    has_profile_pic: Optional[bool] = None
    external_url: Optional[str] = None
    observation_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source_provenance: CollectorSource
    completeness_score: Optional[float] = Field(
        default=None, ge=0.0, le=1.0, description="Completeness ratio between 0.0 and 1.0"
    )


class OverallCollectionStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"


class CollectionResult(BaseModel):
    request_id: str
    target: AccountTarget
    overall_status: OverallCollectionStatus = OverallCollectionStatus.NOT_STARTED
    sources: Dict[CollectorSource, DataSourceStatus] = Field(default_factory=dict)
    observations: List[AccountObservation] = Field(default_factory=list)
    missing_data_summary: List[str] = Field(default_factory=list)
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
