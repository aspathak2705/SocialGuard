from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class FeatureContribution(BaseModel):
    feature_name: str
    feature_value: float
    contribution: float = Field(..., description="SHAP attribution for target class")
    direction: str = Field(..., description="'fake' or 'genuine' alignment")
    display_name: Optional[str] = None
    description: Optional[str] = None


class KeyFactor(BaseModel):
    feature_name: str
    display_name: str
    direction: str
    contribution_value: float
    explanation: str


class ExplanationResult(BaseModel):
    status: str = Field(..., description="'available', 'fallback', 'evidence_only', or 'unavailable'")
    provider: str = Field(default="deterministic", description="'openrouter_nemotron', 'deterministic_fallback', 'evidence_only', 'unavailable'")
    model_id: str = Field(default="SHAP Explainer", description="Model/method identifier")
    method: str = Field(default="SHAP Explainer", description="Attribution algorithm")
    summary: str = Field(default="", description="Plain-language human-readable synthesis")
    key_factors: List[KeyFactor] = Field(default_factory=list)
    conflicting_signals: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    review_guidance: List[str] = Field(default_factory=list)
    contributions: List[FeatureContribution] = Field(default_factory=list)
    top_drivers: List[str] = Field(default_factory=list)
    warning: Optional[str] = None



class EvidenceItem(BaseModel):
    field_name: str
    observed_value: Any
    source: str
    observation_id: Optional[str] = None
    timestamp: Optional[datetime] = None


class PredictAccountRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=255, description="Target Instagram username")
    run_id: Optional[str] = Field(default=None, description="Optional previous collection run ID")


class PredictionAssessment(BaseModel):
    request_id: str
    target_username: str
    predicted_class: str = Field(..., description="'fake' or 'genuine'")
    fake_probability: float = Field(..., ge=0.0, le=1.0, description="Raw model probability for fake class")
    score_label: str = Field(default="Uncalibrated Probability", description="Score semantics")
    decision_threshold: float = Field(default=0.5, description="Decision threshold applied")
    model_id: str
    pipeline_version: str
    verification_status: str = Field(..., description="'PROVISIONAL' or 'APPROVED'")
    verification_note: str
    feature_coverage_ratio: float = Field(..., ge=0.0, le=1.0)
    missing_features: List[str] = Field(default_factory=list)
    extracted_features: Dict[str, float] = Field(default_factory=dict)
    evidence: List[EvidenceItem] = Field(default_factory=list)
    explanation: ExplanationResult
    warnings: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    processing_time_ms: float
