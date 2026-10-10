from typing import Dict, List
from app.collectors.base import BaseCollector
from app.collectors.instaloader_collector import InstaloaderCollector
from app.collectors.gallery_dl_collector import GalleryDlCollector
from app.collectors.playwright_collector import PlaywrightCollector
from app.schemas.collection import CollectorSource
from app.core.config import settings


class CollectorRegistry:
    """Manages active and configured data collection adapters."""

    def __init__(self):
        self._collectors: Dict[CollectorSource, BaseCollector] = {}
        self._initialize_adapters()

    def _initialize_adapters(self) -> None:
        if settings.COLLECTOR_INSTALOADER_ENABLED:
            self._collectors[CollectorSource.INSTALOADER] = InstaloaderCollector()

        if settings.COLLECTOR_GALLERY_DL_ENABLED:
            self._collectors[CollectorSource.GALLERY_DL] = GalleryDlCollector()

        if settings.COLLECTOR_PLAYWRIGHT_ENABLED:
            self._collectors[CollectorSource.PLAYWRIGHT] = PlaywrightCollector()

    def get_collector(self, source: CollectorSource) -> BaseCollector:
        return self._collectors.get(source)

    def get_all_collectors(self) -> List[BaseCollector]:
        return list(self._collectors.values())

    def register(self, collector: BaseCollector) -> None:
        self._collectors[collector.source] = collector


default_registry = CollectorRegistry()
