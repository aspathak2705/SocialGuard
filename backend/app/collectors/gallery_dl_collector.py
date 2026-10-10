import asyncio
import json
import logging
import shutil
import sys
import time
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from app.collectors.base import BaseCollector
from app.schemas.account import AccountTarget
from app.schemas.collection import (
    CollectorSource,
    CollectorCapability,
    DataSourceStatus,
    DataSourceExecutionStatus,
    AccountObservation,
)

logger = logging.getLogger("socialguard.collectors.gallery_dl")


class GalleryDlCollector(BaseCollector):
    """
    Subprocess-isolated adapter using gallery-dl for public media structure and metadata inspection.
    Uses safe argument array (shell=False), bounds output size, and enforces timeouts.
    """

    @property
    def source(self) -> CollectorSource:
        return CollectorSource.GALLERY_DL

    @property
    def capabilities(self) -> List[CollectorCapability]:
        return [CollectorCapability.MEDIA_METADATA, CollectorCapability.POST_METADATA]

    def is_available(self) -> Tuple[bool, Optional[str]]:
        # gallery-dl can be run via python -m gallery_dl or as standalone executable
        try:
            import gallery_dl  # noqa
            return True, None
        except ImportError:
            if shutil.which("gallery-dl"):
                return True, None
            return False, "gallery-dl executable or python module not found."

    async def collect(
        self,
        target: AccountTarget,
        timeout_seconds: float = 12.0,
    ) -> Tuple[DataSourceStatus, Optional[AccountObservation]]:
        available, reason = self.is_available()
        if not available:
            return (
                DataSourceStatus(
                    source=self.source,
                    status=DataSourceExecutionStatus.UNAVAILABLE,
                    error_code="DEPENDENCY_MISSING",
                    error_message=reason,
                    collection_timestamp=datetime.now(timezone.utc),
                ),
                None,
            )

        start_time = time.perf_counter()
        capabilities_attempted = self.capabilities

        # Build safe subprocess args: dump metadata simulation without downloading files
        cmd = [
            sys.executable,
            "-m",
            "gallery_dl",
            "--dump-json",
            "--range",
            "1-3",  # Sample at most 3 items to bound execution
            target.canonical_profile_url,
        ]

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                proc.communicate(),
                timeout=timeout_seconds,
            )
            elapsed = (time.perf_counter() - start_time) * 1000

            stdout_text = stdout_bytes.decode("utf-8", errors="replace").strip()
            stderr_text = stderr_bytes.decode("utf-8", errors="replace").strip()

            if proc.returncode != 0:
                # Analyze common gallery-dl failure modes
                error_msg = "gallery-dl acquisition returned non-zero status."
                error_code = "SUBPROCESS_ERROR"

                if "429" in stderr_text or "rate limit" in stderr_text.lower():
                    error_code = "RATE_LIMITED"
                    error_msg = "Rate limit encountered during media metadata acquisition."
                elif "login" in stderr_text.lower() or "authentication" in stderr_text.lower():
                    error_code = "AUTH_REQUIRED"
                    error_msg = "Instagram authentication required for media metadata access."

                return (
                    DataSourceStatus(
                        source=self.source,
                        status=DataSourceExecutionStatus.FAILED,
                        duration_ms=round(elapsed, 2),
                        capabilities_attempted=capabilities_attempted,
                        error_code=error_code,
                        error_message=error_msg,
                        retryable=(error_code == "RATE_LIMITED"),
                        collection_timestamp=datetime.now(timezone.utc),
                    ),
                    None,
                )

            # Parse JSON metadata if present
            sample_data = {}
            if stdout_text:
                for line in stdout_text.splitlines():
                    line = line.strip()
                    if line.startswith("[") or line.startswith("{"):
                        try:
                            parsed = json.loads(line)
                            if isinstance(parsed, list) and len(parsed) >= 2:
                                sample_data = parsed[1] if isinstance(parsed[1], dict) else {}
                                break
                            elif isinstance(parsed, dict):
                                sample_data = parsed
                                break
                        except Exception:
                            continue

            collected_fields = []
            if sample_data:
                collected_fields = [k for k in ["filename", "date", "description", "extension"] if k in sample_data]

            observation = AccountObservation(
                username=target.normalized_username,
                raw_metadata_sample={"sample_keys": list(sample_data.keys())[:10]} if sample_data else None,
                source_provenance=self.source,
                completeness_score=0.5 if sample_data else 0.0,
            )

            status = DataSourceStatus(
                source=self.source,
                status=DataSourceExecutionStatus.SUCCESS if sample_data else DataSourceExecutionStatus.PARTIAL,
                duration_ms=round(elapsed, 2),
                capabilities_attempted=capabilities_attempted,
                collected_field_names=collected_fields,
                missing_field_names=["full_media_dump_skipped_in_phase_2"],
                collection_timestamp=datetime.now(timezone.utc),
            )
            return status, observation

        except asyncio.TimeoutError:
            elapsed = (time.perf_counter() - start_time) * 1000
            try:
                proc.kill()
                await proc.wait()
            except Exception:
                pass

            return (
                DataSourceStatus(
                    source=self.source,
                    status=DataSourceExecutionStatus.TIMED_OUT,
                    duration_ms=round(elapsed, 2),
                    capabilities_attempted=capabilities_attempted,
                    error_code="TIMEOUT",
                    error_message=f"gallery-dl collection timed out after {timeout_seconds}s.",
                    retryable=True,
                    collection_timestamp=datetime.now(timezone.utc),
                ),
                None,
            )
        except Exception as e:
            elapsed = (time.perf_counter() - start_time) * 1000
            logger.warning(f"gallery-dl execution error for @{target.normalized_username}: {e}")
            return (
                DataSourceStatus(
                    source=self.source,
                    status=DataSourceExecutionStatus.FAILED,
                    duration_ms=round(elapsed, 2),
                    capabilities_attempted=capabilities_attempted,
                    error_code="EXECUTION_ERROR",
                    error_message="Subprocess execution error occurred during media inspection.",
                    retryable=False,
                    collection_timestamp=datetime.now(timezone.utc),
                ),
                None,
            )
