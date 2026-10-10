import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

from app.collectors.registry import CollectorRegistry, default_registry
from app.schemas.account import AccountTarget
from app.schemas.collection import (
    CollectorSource,
    DataSourceStatus,
    DataSourceExecutionStatus,
    AccountObservation,
    CollectionResult,
    OverallCollectionStatus,
)
from app.core.config import settings

logger = logging.getLogger("socialguard.orchestrator")


class CollectorOrchestrator:
    """
    Coordinates multi-adapter acquisition:
    - Enforces overall deadline and per-collector timeouts.
    - Preserves partial observations when individual collectors fail.
    - Aggregates statuses deterministically.
    """

    def __init__(self, registry: Optional[CollectorRegistry] = None):
        self.registry = registry or default_registry

    async def execute_collection(
        self,
        target: AccountTarget,
        job_id: Optional[str] = None,
    ) -> CollectionResult:
        request_id = job_id or f"acq-{uuid.uuid4().hex[:12]}"
        created_at = datetime.now(timezone.utc)
        collectors = self.registry.get_all_collectors()

        sources_status: Dict[CollectorSource, DataSourceStatus] = {}
        observations: List[AccountObservation] = []
        missing_data_summary: List[str] = []

        if not collectors:
            return CollectionResult(
                request_id=request_id,
                target=target,
                overall_status=OverallCollectionStatus.FAILED,
                sources={},
                observations=[],
                missing_data_summary=["No collection adapters enabled in configuration."],
                error_message="No acquisition collectors are currently enabled.",
                created_at=created_at,
                completed_at=datetime.now(timezone.utc),
            )

        # Semaphores to bound concurrent executions
        semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_COLLECTORS)

        async def _run_collector(collector):
            async with semaphore:
                try:
                    return await collector.collect(
                        target=target,
                        timeout_seconds=settings.COLLECTOR_TIMEOUT_SECONDS,
                    )
                except Exception as exc:
                    logger.error(f"Unexpected error running collector {collector.source}: {exc}")
                    status = DataSourceStatus(
                        source=collector.source,
                        status=DataSourceExecutionStatus.FAILED,
                        error_code="INTERNAL_COLLECTOR_ERROR",
                        error_message="Unexpected error occurred inside adapter.",
                        collection_timestamp=datetime.now(timezone.utc),
                    )
                    return status, None

        tasks = [asyncio.create_task(_run_collector(c)) for c in collectors]

        try:
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=settings.OVERALL_ACQUISITION_TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError:
            logger.warning(f"Acquisition job {request_id} exceeded overall deadline.")
            # Cancel pending
            for t in tasks:
                if not t.done():
                    t.cancel()
            results = []
            for c in collectors:
                results.append((
                    DataSourceStatus(
                        source=c.source,
                        status=DataSourceExecutionStatus.TIMED_OUT,
                        error_code="OVERALL_DEADLINE_EXCEEDED",
                        error_message="Job exceeded maximum overall acquisition deadline.",
                        collection_timestamp=datetime.now(timezone.utc),
                    ),
                    None,
                ))

        # Process results
        for item in results:
            if isinstance(item, Exception):
                continue
            if isinstance(item, tuple) and len(item) == 2:
                status, observation = item
                sources_status[status.source] = status
                if observation:
                    observations.append(observation)
                if status.missing_field_names:
                    missing_data_summary.extend(status.missing_field_names)

        # Determine overall status
        statuses = [s.status for s in sources_status.values()]
        if any(s == DataSourceExecutionStatus.SUCCESS for s in statuses):
            if any(s in (DataSourceExecutionStatus.FAILED, DataSourceExecutionStatus.PARTIAL, DataSourceExecutionStatus.TIMED_OUT) for s in statuses):
                overall = OverallCollectionStatus.PARTIAL
            else:
                overall = OverallCollectionStatus.COMPLETED
        elif any(s == DataSourceExecutionStatus.PARTIAL for s in statuses):
            overall = OverallCollectionStatus.PARTIAL
        elif all(s == DataSourceExecutionStatus.TIMED_OUT for s in statuses):
            overall = OverallCollectionStatus.TIMED_OUT
        else:
            overall = OverallCollectionStatus.FAILED

        # Deduplicate missing data summary
        unique_missing = list(dict.fromkeys(missing_data_summary))

        return CollectionResult(
            request_id=request_id,
            target=target,
            overall_status=overall,
            sources=sources_status,
            observations=observations,
            missing_data_summary=unique_missing,
            created_at=created_at,
            completed_at=datetime.now(timezone.utc),
        )


default_orchestrator = CollectorOrchestrator()
