import logging
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from app.schemas.account import AccountTarget
from app.schemas.collection import CollectionResult, CollectorSource
from app.schemas.pipeline import (
    UnifiedCollectionRun,
    CanonicalObservation,
    DataQualitySummary,
)
from app.pipeline.normalizers import (
    InstaloaderNormalizer,
    GalleryDlNormalizer,
    PlaywrightNormalizer,
)
from app.pipeline.deduplication import DeduplicationEngine

from app.db.session import SessionLocal
from app.db.repositories import PipelineRepository

logger = logging.getLogger("socialguard.pipeline")


class UnifiedPipelineService:
    """
    Coordinates normalization, validation, deduplication, and quality assessment.
    Persists durable records to Supabase / PostgreSQL / SQLite storage.
    """

    def __init__(self):
        self.instaloader_norm = InstaloaderNormalizer()
        self.gallery_dl_norm = GalleryDlNormalizer()
        self.playwright_norm = PlaywrightNormalizer()
        self._runs = {}

    def get_run(self, run_id: str) -> Optional[UnifiedCollectionRun]:
        # 1. Check in-memory fast cache
        if run_id in self._runs:
            return self._runs[run_id]

        # 2. Check durable database repository
        try:
            with SessionLocal() as db:
                db_run = PipelineRepository.get_unified_run(db, run_id)
                if db_run:
                    from app.schemas.account import AccountTarget, TargetInputType
                    from app.schemas.collection import OverallCollectionStatus, DataSourceStatus, CollectorSource
                    from app.schemas.pipeline import DataQualitySummary, CanonicalObservation, ObservationType, FieldValueMetadata, FieldAvailabilityStatus

                    # Reconstruct UnifiedCollectionRun
                    target = AccountTarget(
                        original_input=db_run.original_input,
                        normalized_username=db_run.target_username,
                        canonical_profile_url=db_run.canonical_profile_url,
                        input_type=TargetInputType(db_run.input_type),
                    )
                    source_executions = {
                        CollectorSource(k): DataSourceStatus(**v) for k, v in (db_run.source_executions or {}).items()
                    }
                    canonical_obs = []
                    for o in db_run.observations:
                        f_meta = {
                            fk: FieldValueMetadata(**fv) for fk, fv in (o.field_metadata or {}).items()
                        }
                        canonical_obs.append(
                            CanonicalObservation(
                                observation_id=o.observation_id,
                                observation_type=ObservationType(o.observation_type),
                                target_username=o.target_username,
                                source=CollectorSource(o.source),
                                source_record_id=o.source_record_id,
                                observation_timestamp=o.observation_timestamp,
                                normalization_timestamp=o.normalization_timestamp,
                                account_id=o.account_id,
                                full_name=o.full_name,
                                biography=o.biography,
                                is_private=o.is_private,
                                is_verified=o.is_verified,
                                posts_count=o.posts_count,
                                followers_count=o.followers_count,
                                following_count=o.following_count,
                                has_profile_pic=o.has_profile_pic,
                                external_url=o.external_url,
                                field_metadata=f_meta,
                                validation_warnings=o.validation_warnings or [],
                                is_duplicate=o.is_duplicate,
                                duplicate_of=o.duplicate_of,
                            )
                        )
                    quality_summary = DataQualitySummary(**(db_run.quality_summary or {}))
                    restored_run = UnifiedCollectionRun(
                        run_id=db_run.run_id,
                        target=target,
                        overall_status=OverallCollectionStatus(db_run.overall_status),
                        pipeline_version=db_run.pipeline_version,
                        created_at=db_run.created_at,
                        completed_at=db_run.completed_at,
                        source_executions=source_executions,
                        canonical_observations=canonical_obs,
                        quality_summary=quality_summary,
                        missing_data_summary=db_run.missing_data_summary or [],
                        errors=db_run.errors or [],
                    )
                    self._runs[run_id] = restored_run
                    return restored_run
        except Exception as e:
            logger.warning(f"Error querying database for run_id '{run_id}': {e}")

        return None



    def process_acquisition_result(
        self,
        collection_result: CollectionResult,
    ) -> UnifiedCollectionRun:
        run_id = f"run-{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc)

        raw_count = len(collection_result.observations)
        canonical_list: List[CanonicalObservation] = []
        all_warnings: List[str] = []
        invalid_count = 0

        source_breakdown = {}

        for obs in collection_result.observations:
            src = obs.source_provenance
            source_breakdown.setdefault(src, {"raw": 0, "valid": 0, "invalid": 0})
            source_breakdown[src]["raw"] += 1

            try:
                if src == CollectorSource.INSTALOADER:
                    canonical, warns = self.instaloader_norm.normalize(obs)
                elif src == CollectorSource.GALLERY_DL:
                    canonical, warns = self.gallery_dl_norm.normalize(obs)
                elif src == CollectorSource.PLAYWRIGHT:
                    canonical, warns = self.playwright_norm.normalize(obs)
                else:
                    invalid_count += 1
                    source_breakdown[src]["invalid"] += 1
                    continue

                canonical_list.append(canonical)
                all_warnings.extend(warns)
                source_breakdown[src]["valid"] += 1
            except Exception as e:
                logger.error(f"Error normalizing observation from {src}: {e}")
                invalid_count += 1
                source_breakdown[src]["invalid"] += 1
                all_warnings.append(f"Failed to normalize observation from {src}: {str(e)}")

        # Deduplicate
        deduped_obs, dup_count = DeduplicationEngine.deduplicate(canonical_list)
        retained_count = len([o for o in deduped_obs if not o.is_duplicate])

        # Compute completeness ratio over expected fields (for profile)
        completeness = None
        profile_obs = [o for o in deduped_obs if o.account_id or o.full_name or o.followers_count is not None]
        if profile_obs:
            first_p = profile_obs[0]
            observed_fields = len([m for m in first_p.field_metadata.values() if m.status.value == "observed"])
            total_expected = len(first_p.field_metadata)
            if total_expected > 0:
                completeness = round(observed_fields / total_expected, 2)

        quality_summary = DataQualitySummary(
            raw_records_received=raw_count,
            valid_normalized_records=len(deduped_obs),
            invalid_records_rejected=invalid_count,
            duplicate_records_detected=dup_count,
            retained_records=retained_count,
            completeness_score=completeness,
            source_breakdown=source_breakdown,
            warnings=all_warnings,
        )

        unified_run = UnifiedCollectionRun(
            run_id=run_id,
            target=collection_result.target,
            overall_status=collection_result.overall_status,
            pipeline_version="3.0.0",
            created_at=collection_result.created_at,
            completed_at=now,
            source_executions=collection_result.sources,
            canonical_observations=deduped_obs,
            quality_summary=quality_summary,
            missing_data_summary=collection_result.missing_data_summary,
            errors=[collection_result.error_message] if collection_result.error_message else [],
        )
        self._runs[run_id] = unified_run

        # Persist to database repository
        try:
            with SessionLocal() as db:
                PipelineRepository.save_unified_run(db, unified_run)
        except Exception as e:
            logger.warning(f"Could not persist run to database repository: {e}")

        return unified_run




pipeline_service = UnifiedPipelineService()
