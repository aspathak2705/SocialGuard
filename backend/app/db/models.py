from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    JSON,
    Text,
    Index,
)
from sqlalchemy.orm import relationship
from app.db.session import Base


class CollectionRunModel(Base):
    """Stores acquisition and pipeline execution runs."""
    __tablename__ = "collection_runs"

    run_id = Column(String(64), primary_key=True, index=True)
    target_username = Column(String(255), nullable=False, index=True)
    original_input = Column(String(512), nullable=False)
    canonical_profile_url = Column(String(512), nullable=False)
    input_type = Column(String(32), nullable=False)
    overall_status = Column(String(32), nullable=False)
    pipeline_version = Column(String(32), default="3.0.0")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Serialized dictionaries
    source_executions = Column(JSON, nullable=False, default=dict)
    quality_summary = Column(JSON, nullable=False, default=dict)
    missing_data_summary = Column(JSON, nullable=False, default=list)
    errors = Column(JSON, nullable=False, default=list)

    # Relationships
    observations = relationship("CanonicalObservationModel", back_populates="run", cascade="all, delete-orphan")
    assessments = relationship("AssessmentModel", back_populates="run", cascade="all, delete-orphan")


class CanonicalObservationModel(Base):
    """Stores normalized canonical observations with source provenance."""
    __tablename__ = "canonical_observations"

    observation_id = Column(String(64), primary_key=True, index=True)
    run_id = Column(String(64), ForeignKey("collection_runs.run_id"), nullable=False, index=True)
    target_username = Column(String(255), nullable=False, index=True)
    observation_type = Column(String(32), nullable=False)
    source = Column(String(64), nullable=False)
    source_record_id = Column(String(255), nullable=True)
    observation_timestamp = Column(DateTime(timezone=True), nullable=True)
    normalization_timestamp = Column(DateTime(timezone=True), nullable=True)

    # Core Normalized Attributes
    account_id = Column(String(128), nullable=True)
    full_name = Column(String(255), nullable=True)
    biography = Column(Text, nullable=True)
    is_private = Column(Boolean, nullable=True)
    is_verified = Column(Boolean, nullable=True)
    posts_count = Column(Integer, nullable=True)
    followers_count = Column(Integer, nullable=True)
    following_count = Column(Integer, nullable=True)
    has_profile_pic = Column(Boolean, nullable=True)
    external_url = Column(String(512), nullable=True)

    # Granular Field Metadata & Warnings
    field_metadata = Column(JSON, nullable=False, default=dict)
    validation_warnings = Column(JSON, nullable=False, default=list)
    is_duplicate = Column(Boolean, default=False)
    duplicate_of = Column(String(64), nullable=True)

    # Relationships
    run = relationship("CollectionRunModel", back_populates="observations")


class AssessmentModel(Base):
    """Stores model prediction assessments."""
    __tablename__ = "investigation_assessments"

    request_id = Column(String(64), primary_key=True, index=True)
    run_id = Column(String(64), ForeignKey("collection_runs.run_id"), nullable=True, index=True)
    target_username = Column(String(255), nullable=False, index=True)
    predicted_class = Column(String(32), nullable=False)
    fake_probability = Column(Float, nullable=False)
    score_label = Column(String(64), nullable=False)
    decision_threshold = Column(Float, nullable=False, default=0.5)
    model_id = Column(String(64), nullable=False)
    pipeline_version = Column(String(32), default="5.0.0")
    verification_status = Column(String(32), nullable=False)
    verification_note = Column(Text, nullable=False)
    feature_coverage_ratio = Column(Float, nullable=False)
    missing_features = Column(JSON, nullable=False, default=list)
    extracted_features = Column(JSON, nullable=False, default=dict)
    evidence = Column(JSON, nullable=False, default=list)
    warnings = Column(JSON, nullable=False, default=list)
    processing_time_ms = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    # Relationships
    run = relationship("CollectionRunModel", back_populates="assessments")
    explanation = relationship("ExplanationModel", uselist=False, back_populates="assessment", cascade="all, delete-orphan")


class ExplanationModel(Base):
    """Stores human-readable and SHAP explanations."""
    __tablename__ = "investigation_explanations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    assessment_id = Column(String(64), ForeignKey("investigation_assessments.request_id"), nullable=False, unique=True, index=True)
    status = Column(String(32), nullable=False)
    provider = Column(String(64), nullable=False)
    model = Column(String(128), nullable=False)
    summary = Column(Text, nullable=False)
    key_factors = Column(JSON, nullable=False, default=list)
    conflicting_signals = Column(JSON, nullable=False, default=list)
    limitations = Column(JSON, nullable=False, default=list)
    review_guidance = Column(JSON, nullable=False, default=list)
    raw_contributions = Column(JSON, nullable=False, default=list)
    warning = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    assessment = relationship("AssessmentModel", back_populates="explanation")


# Composite indexes
Index("idx_run_target_time", CollectionRunModel.target_username, CollectionRunModel.created_at)
Index("idx_assessment_target_time", AssessmentModel.target_username, AssessmentModel.created_at)
