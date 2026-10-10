from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.schemas.account import AccountTarget
from app.schemas.collection import CollectorSource, DataSourceStatus, OverallCollectionStatus


class ObservationType(str, Enum):
    PROFILE = "profile"
    MEDIA = "media"
    POST = "post"
    BROWSER_DOM = "browser_dom"


class FieldAvailabilityStatus(str, Enum):
    OBSERVED = "observed"
    NOT_RETURNED = "not_returned"
    UNAVAILABLE = "unavailable"
    NOT_APPLICABLE = "not_applicable"
    INVALID = "invalid"


class FieldValueMetadata(BaseModel):
    field_name: str
    status: FieldAvailabilityStatus
    raw_value: Optional[Any] = None
    detail: Optional[str] = None


class CanonicalObservation(BaseModel):
    """
    Normalized, schema-validated observation record with strict provenance.
    """
    observation_id: str
    observation_type: ObservationType
    target_username: str
    source: CollectorSource
    source_record_id: Optional[str] = None
    observation_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    normalization_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Core Normalized Attributes
    account_id: Optional[str] = None
    full_name: Optional[str] = None
    biography: Optional[str] = None
    is_private: Optional[bool] = None
    is_verified: Optional[bool] = None
    posts_count: Optional[int] = None
    followers_count: Optional[int] = None
    following_count: Optional[int] = None
    has_profile_pic: Optional[bool] = None
    external_url: Optional[str] = None

    # Granular Field Metadata
    field_metadata: Dict[str, FieldValueMetadata] = Field(default_factory=dict)
    validation_warnings: List[str] = Field(default_factory=list)
    is_duplicate: bool = False
    duplicate_of: Optional[str] = None


class DataQualitySummary(BaseModel):
    raw_records_received: int = 0
    valid_normalized_records: int = 0
    invalid_records_rejected: int = 0
    duplicate_records_detected: int = 0
    retained_records: int = 0
    completeness_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    source_breakdown: Dict[CollectorSource, Dict[str, int]] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)


class UnifiedCollectionRun(BaseModel):
    """
    Encompassing response model for the unified data pipeline (Phase 3).
    """
    run_id: str
    target: AccountTarget
    overall_status: OverallCollectionStatus
    pipeline_version: str = "3.0.0"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    source_executions: Dict[CollectorSource, DataSourceStatus] = Field(default_factory=dict)
    canonical_observations: List[CanonicalObservation] = Field(default_factory=list)
    quality_summary: DataQualitySummary = Field(default_factory=DataQualitySummary)
    missing_data_summary: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
