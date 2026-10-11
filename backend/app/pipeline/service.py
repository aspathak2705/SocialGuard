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

logger = logging.getLogger("socialguard.pipeline")


class UnifiedPipelineService:
    """
    Coordinates normalization, validation, deduplication, and quality assessment.
    """

    def __init__(self):
        self.instaloader_norm = InstaloaderNormalizer()
        self.gallery_dl_norm = GalleryDlNormalizer()
        self.playwright_norm = PlaywrightNormalizer()
        self._runs = {}

    def get_run(self, run_id: str) -> Optional[UnifiedCollectionRun]:
        return self._runs.get(run_id)


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
        return unified_run



pipeline_service = UnifiedPipelineService()
