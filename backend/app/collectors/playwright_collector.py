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

logger = logging.getLogger("socialguard.collectors.playwright")


class PlaywrightCollector(BaseCollector):
    """
    Browser-based collector adapter using Playwright.
    Enforces URL destination checks, no stealth/bypass hacks, bounded execution, and reliable resource cleanup.
    """

    @property
    def source(self) -> CollectorSource:
        return CollectorSource.PLAYWRIGHT

    @property
    def capabilities(self) -> List[CollectorCapability]:
        return [CollectorCapability.BROWSER_RENDER]

    def is_available(self) -> Tuple[bool, Optional[str]]:
        try:
            import playwright  # noqa
            # Note: browser binaries might still need playwright install chromium
            return True, None
        except ImportError:
            return False, "playwright library is not installed."

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
            from playwright.async_api import async_playwright

            async with async_playwright() as p:
                browser = None
                try:
                    browser = await p.chromium.launch(headless=True)
                except Exception as launch_err:
                    elapsed = (time.perf_counter() - start_time) * 1000
                    return (
                        DataSourceStatus(
                            source=self.source,
                            status=DataSourceExecutionStatus.UNAVAILABLE,
                            duration_ms=round(elapsed, 2),
                            capabilities_attempted=capabilities_attempted,
                            error_code="BROWSER_BINARY_MISSING",
                            error_message="Playwright browser binary (chromium) not installed. Run 'playwright install chromium' to enable.",
                            retryable=False,
                            collection_timestamp=datetime.now(timezone.utc),
                        ),
                        None,
                    )

                context = await browser.new_context(
                    viewport={"width": 1280, "height": 800},
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                )
                page = await context.new_page()

                # Safety: ensure destination is exact canonical URL
                response = await page.goto(
                    target.canonical_profile_url,
                    timeout=int(timeout_seconds * 1000),
                    wait_until="domcontentloaded",
                )

                # Validate final redirected URL hasn't been hijacked to disallowed domain
                final_url = page.url
                if not ("instagram.com" in final_url):
                    await context.close()
                    await browser.close()
                    elapsed = (time.perf_counter() - start_time) * 1000
                    return (
                        DataSourceStatus(
                            source=self.source,
                            status=DataSourceExecutionStatus.FAILED,
                            duration_ms=round(elapsed, 2),
                            capabilities_attempted=capabilities_attempted,
                            error_code="UNEXPECTED_REDIRECT",
                            error_message=f"Browser redirected to unexpected destination: {final_url}",
                            retryable=False,
                            collection_timestamp=datetime.now(timezone.utc),
                        ),
                        None,
                    )

                page_title = await page.title()
                status_code = response.status if response else 200

                await context.close()
                await browser.close()
                elapsed = (time.perf_counter() - start_time) * 1000

                # Check if login wall was encountered
                if "login" in page_title.lower() or status_code in (401, 403):
                    return (
                        DataSourceStatus(
                            source=self.source,
                            status=DataSourceExecutionStatus.PARTIAL,
                            duration_ms=round(elapsed, 2),
                            capabilities_attempted=capabilities_attempted,
                            collected_field_names=["page_title", "status_code"],
                            error_code="LOGIN_WALL_ENCOUNTERED",
                            error_message="Instagram presented a login barrier for unauthenticated browser session.",
                            retryable=False,
                            collection_timestamp=datetime.now(timezone.utc),
                        ),
                        AccountObservation(
                            username=target.normalized_username,
                            raw_metadata_sample={"title": page_title, "status": status_code},
                            source_provenance=self.source,
                            completeness_score=0.2,
                        ),
                    )

                return (
                    DataSourceStatus(
                        source=self.source,
                        status=DataSourceExecutionStatus.SUCCESS,
                        duration_ms=round(elapsed, 2),
                        capabilities_attempted=capabilities_attempted,
                        collected_field_names=["page_title", "dom_content"],
                        collection_timestamp=datetime.now(timezone.utc),
                    ),
                    AccountObservation(
                        username=target.normalized_username,
                        raw_metadata_sample={"title": page_title},
                        source_provenance=self.source,
                        completeness_score=0.5,
                    ),
                )

        except asyncio.TimeoutError:
            elapsed = (time.perf_counter() - start_time) * 1000
            return (
                DataSourceStatus(
                    source=self.source,
                    status=DataSourceExecutionStatus.TIMED_OUT,
                    duration_ms=round(elapsed, 2),
                    capabilities_attempted=capabilities_attempted,
                    error_code="TIMEOUT",
                    error_message=f"Playwright navigation timed out after {timeout_seconds}s.",
                    retryable=True,
                    collection_timestamp=datetime.now(timezone.utc),
                ),
                None,
            )
        except Exception as e:
            elapsed = (time.perf_counter() - start_time) * 1000
            logger.warning(f"Playwright execution error for @{target.normalized_username}: {e}")
            return (
                DataSourceStatus(
                    source=self.source,
                    status=DataSourceExecutionStatus.FAILED,
                    duration_ms=round(elapsed, 2),
                    capabilities_attempted=capabilities_attempted,
                    error_code="BROWSER_ERROR",
                    error_message="Playwright browser session failed during inspection.",
                    retryable=False,
                    collection_timestamp=datetime.now(timezone.utc),
                ),
                None,
            )
