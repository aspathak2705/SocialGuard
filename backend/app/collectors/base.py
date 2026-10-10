from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
from app.schemas.account import AccountTarget
from app.schemas.collection import (
    CollectorSource,
    CollectorCapability,
    DataSourceStatus,
    AccountObservation,
)


class BaseCollector(ABC):
    """
    Abstract interface for SocialGuard data acquisition adapters.
    Each adapter isolates third-party tooling, declares exact capabilities,
    and returns a structured outcome envelope.
    """

    @property
    @abstractmethod
    def source(self) -> CollectorSource:
        """Unique identifier of the collector source."""
        pass

    @property
    @abstractmethod
    def capabilities(self) -> List[CollectorCapability]:
        """Declared collection capabilities for this adapter."""
        pass

    @abstractmethod
    def is_available(self) -> Tuple[bool, Optional[str]]:
        """
        Lightweight check verifying if underlying tool/environment is ready.
        Does not perform expensive network requests.
        Returns: (is_ready, optional_reason_if_not)
        """
        pass

    @abstractmethod
    async def collect(
        self,
        target: AccountTarget,
        timeout_seconds: float = 12.0,
    ) -> Tuple[DataSourceStatus, Optional[AccountObservation]]:
        """
        Executes bounded, safe acquisition for the specified canonical target.
        Returns: (data_source_status, optional_account_observation)
        """
        pass
