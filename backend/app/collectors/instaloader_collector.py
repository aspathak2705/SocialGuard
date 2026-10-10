import asyncio
import logging
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

logger = logging.getLogger("socialguard.collectors.instaloader")


class InstaloaderCollector(BaseCollector):
    """
    Collector adapter using Instaloader to acquire public profile metadata.
    Enforces timeout, non-blocking executor execution, and distinguishes missing vs restricted fields.
    """

    @property
    def source(self) -> CollectorSource:
        return CollectorSource.INSTALOADER

    @property
    def capabilities(self) -> List[CollectorCapability]:
        return [CollectorCapability.PROFILE_METADATA]

    def is_available(self) -> Tuple[bool, Optional[str]]:
        try:
            import instaloader  # noqa
            return True, None
        except ImportError:
            return False, "instaloader library is not installed in the environment."

    def _sync_fetch_metadata(self, username: str) -> dict:
        """
        Synchronous execution inside worker thread.
        Never downloads full media; reads public metadata structure.
        """
        import instaloader
        from instaloader.exceptions import (
            ProfileNotExistsException,
            ConnectionException,
            QueryReturnedBadRequestException,
            QueryReturnedNotFoundException,
            LoginRequiredException,
        )

        L = instaloader.Instaloader(
            download_pictures=False,
            download_videos=False,
            download_video_thumbnails=False,
            download_geotags=False,
            download_comments=False,
            save_metadata=False,
            compress_json=False,
            request_timeout=8.0,
        )

        try:
            profile = instaloader.Profile.from_username(L.context, username)
            return {
                "account_id": str(profile.userid) if profile.userid else None,
                "username": profile.username,
                "full_name": profile.full_name,
                "biography": profile.biography,
                "is_private": bool(profile.is_private),
                "is_verified": bool(profile.is_verified),
                "posts_count": int(profile.mediacount) if profile.mediacount is not None else None,
                "followers_count": int(profile.followers) if profile.followers is not None else None,
                "following_count": int(profile.followees) if profile.followees is not None else None,
                "has_profile_pic": bool(profile.has_profile_pic),
                "external_url": profile.external_url,
            }
        except (ProfileNotExistsException, QueryReturnedNotFoundException):
            raise ValueError(f"Instagram profile '{username}' does not exist.")
        except LoginRequiredException:
            raise PermissionError("Access restricted: Instagram requires authentication for this profile.")
        except (ConnectionException, QueryReturnedBadRequestException) as e:
            raise ConnectionError(f"Network or platform restriction encountered: {str(e)}")

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

        try:
            loop = asyncio.get_running_loop()
            metadata = await asyncio.wait_for(
                loop.run_in_executor(None, self._sync_fetch_metadata, target.normalized_username),
                timeout=timeout_seconds,
            )
            elapsed = (time.perf_counter() - start_time) * 1000

            collected_fields = [k for k, v in metadata.items() if v is not None]
            all_expected = [
                "account_id", "username", "full_name", "biography", "is_private",
                "is_verified", "posts_count", "followers_count", "following_count",
                "has_profile_pic", "external_url"
            ]
            missing_fields = [k for k in all_expected if k not in collected_fields]

            observation = AccountObservation(
                account_id=metadata.get("account_id"),
                username=target.normalized_username,
                full_name=metadata.get("full_name"),
                biography=metadata.get("biography"),
                is_private=metadata.get("is_private"),
                is_verified=metadata.get("is_verified"),
                posts_count=metadata.get("posts_count"),
                followers_count=metadata.get("followers_count"),
                following_count=metadata.get("following_count"),
                has_profile_pic=metadata.get("has_profile_pic"),
                external_url=metadata.get("external_url"),
                source_provenance=self.source,
                completeness_score=round(len(collected_fields) / len(all_expected), 2),
            )

            status = DataSourceStatus(
                source=self.source,
                status=DataSourceExecutionStatus.SUCCESS,
                duration_ms=round(elapsed, 2),
                capabilities_attempted=capabilities_attempted,
                collected_field_names=collected_fields,
                missing_field_names=missing_fields,
                collection_timestamp=datetime.now(timezone.utc),
            )
            return status, observation

        except asyncio.TimeoutError:
            elapsed = (time.perf_counter() - start_time) * 1000
            return (
                DataSourceStatus(
                    source=self.source,
                    status=DataSourceExecutionStatus.TIMED_OUT,
                    duration_ms=round(elapsed, 2),
                    capabilities_attempted=capabilities_attempted,
                    error_code="TIMEOUT",
                    error_message=f"Instaloader collection timed out after {timeout_seconds}s.",
                    retryable=True,
                    collection_timestamp=datetime.now(timezone.utc),
                ),
                None,
            )
        except PermissionError as e:
            elapsed = (time.perf_counter() - start_time) * 1000
            return (
                DataSourceStatus(
                    source=self.source,
                    status=DataSourceExecutionStatus.FAILED,
                    duration_ms=round(elapsed, 2),
                    capabilities_attempted=capabilities_attempted,
                    error_code="ACCESS_RESTRICTED",
                    error_message=str(e),
                    retryable=False,
                    collection_timestamp=datetime.now(timezone.utc),
                ),
                None,
            )
        except ValueError as e:
            elapsed = (time.perf_counter() - start_time) * 1000
            return (
                DataSourceStatus(
                    source=self.source,
                    status=DataSourceExecutionStatus.FAILED,
                    duration_ms=round(elapsed, 2),
                    capabilities_attempted=capabilities_attempted,
                    error_code="PROFILE_NOT_FOUND",
                    error_message=str(e),
                    retryable=False,
                    collection_timestamp=datetime.now(timezone.utc),
                ),
                None,
            )
        except Exception as e:
            elapsed = (time.perf_counter() - start_time) * 1000
            logger.warning(f"Instaloader collector error for @{target.normalized_username}: {e}")
            return (
                DataSourceStatus(
                    source=self.source,
                    status=DataSourceExecutionStatus.FAILED,
                    duration_ms=round(elapsed, 2),
                    capabilities_attempted=capabilities_attempted,
                    error_code="ACQUISITION_ERROR",
                    error_message="Unable to acquire data via Instaloader due to network or platform restrictions.",
                    retryable=True,
                    collection_timestamp=datetime.now(timezone.utc),
                ),
                None,
            )
