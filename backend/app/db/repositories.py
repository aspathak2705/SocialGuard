from typing import Optional, List
from sqlalchemy.orm import Session
from app.db.models import (
    CollectionRunModel,
    CanonicalObservationModel,
    AssessmentModel,
    ExplanationModel,
)
from app.schemas.pipeline import UnifiedCollectionRun, CanonicalObservation
from app.schemas.prediction import PredictionAssessment, ExplanationResult


class PipelineRepository:
    """Handles durable persistence and retrieval of pipeline runs and observations."""

    @staticmethod
    def save_unified_run(db: Session, run: UnifiedCollectionRun) -> CollectionRunModel:
        # Check if already exists (idempotency)
        existing = db.query(CollectionRunModel).filter(CollectionRunModel.run_id == run.run_id).first()
        if existing:
            return existing

        db_run = CollectionRunModel(
            run_id=run.run_id,
            target_username=run.target.normalized_username,
            original_input=run.target.original_input,
            canonical_profile_url=run.target.canonical_profile_url,
            input_type=run.target.input_type,
            overall_status=run.overall_status.value if hasattr(run.overall_status, "value") else str(run.overall_status),
            pipeline_version=run.pipeline_version,
            created_at=run.created_at,
            completed_at=run.completed_at,
            source_executions={k.value if hasattr(k, "value") else str(k): v.model_dump(mode="json") for k, v in run.source_executions.items()},
            quality_summary=run.quality_summary.model_dump(mode="json"),
            missing_data_summary=run.missing_data_summary,
            errors=run.errors,
        )
        db.add(db_run)

        # Save canonical observations
        for obs in run.canonical_observations:
            db_obs = CanonicalObservationModel(
                observation_id=obs.observation_id,
                run_id=run.run_id,
                target_username=obs.target_username,
                observation_type=obs.observation_type.value if hasattr(obs.observation_type, "value") else str(obs.observation_type),
                source=obs.source.value if hasattr(obs.source, "value") else str(obs.source),
                source_record_id=obs.source_record_id,
                observation_timestamp=obs.observation_timestamp,
                normalization_timestamp=obs.normalization_timestamp,
                account_id=obs.account_id,
                full_name=obs.full_name,
                biography=obs.biography,
                is_private=obs.is_private,
                is_verified=obs.is_verified,
                posts_count=obs.posts_count,
                followers_count=obs.followers_count,
                following_count=obs.following_count,
                has_profile_pic=obs.has_profile_pic,
                external_url=obs.external_url,
                field_metadata={k: v.model_dump(mode="json") for k, v in obs.field_metadata.items()},
                validation_warnings=obs.validation_warnings,
                is_duplicate=obs.is_duplicate,
                duplicate_of=obs.duplicate_of,
            )
            db.add(db_obs)

        db.commit()
        db.refresh(db_run)
        return db_run

    @staticmethod
    def get_unified_run(db: Session, run_id: str) -> Optional[CollectionRunModel]:
        return db.query(CollectionRunModel).filter(CollectionRunModel.run_id == run_id).first()


class AssessmentRepository:
    """Handles durable persistence and retrieval of assessments and explanations."""

    @staticmethod
    def save_assessment(
        db: Session,
        assessment: PredictionAssessment,
        run_id: Optional[str] = None,
    ) -> AssessmentModel:
        existing = db.query(AssessmentModel).filter(AssessmentModel.request_id == assessment.request_id).first()
        if existing:
            return existing

        db_assessment = AssessmentModel(
            request_id=assessment.request_id,
            run_id=run_id,
            target_username=assessment.target_username,
            predicted_class=assessment.predicted_class,
            fake_probability=assessment.fake_probability,
            score_label=assessment.score_label,
            decision_threshold=assessment.decision_threshold,
            model_id=assessment.model_id,
            pipeline_version=assessment.pipeline_version,
            verification_status=assessment.verification_status,
            verification_note=assessment.verification_note,
            feature_coverage_ratio=assessment.feature_coverage_ratio,
            missing_features=assessment.missing_features,
            extracted_features=assessment.extracted_features,
            evidence=[e.model_dump() for e in assessment.evidence],
            warnings=assessment.warnings,
            processing_time_ms=assessment.processing_time_ms,
            created_at=assessment.created_at,
        )
        db.add(db_assessment)

        # Save Explanation
        expl = assessment.explanation
        db_expl = ExplanationModel(
            assessment_id=assessment.request_id,
            status=expl.status,
            provider=getattr(expl, "provider", "unknown"),
            model=getattr(expl, "model_id", expl.method),
            summary=getattr(expl, "summary", ""),
            key_factors=[f.model_dump() if hasattr(f, "model_dump") else f for f in getattr(expl, "key_factors", [])],
            conflicting_signals=getattr(expl, "conflicting_signals", []),
            limitations=getattr(expl, "limitations", []),
            review_guidance=getattr(expl, "review_guidance", []),
            raw_contributions=[c.model_dump() if hasattr(c, "model_dump") else c for c in expl.contributions],
            warning=expl.warning,
        )
        db.add(db_expl)

        db.commit()
        db.refresh(db_assessment)
        return db_assessment

    @staticmethod
    def get_assessment(db: Session, request_id: str) -> Optional[AssessmentModel]:
        return db.query(AssessmentModel).filter(AssessmentModel.request_id == request_id).first()
