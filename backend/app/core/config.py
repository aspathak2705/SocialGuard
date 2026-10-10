from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import List


class Settings(BaseSettings):
    APP_NAME: str = "SocialGuard"
    APP_ENV: str = "development"
    API_V1_PREFIX: str = "/api/v1"
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    LOG_LEVEL: str = "INFO"
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:5173", "http://127.0.0.1:5173"]
    )

    # Collector Configurations
    COLLECTOR_INSTALOADER_ENABLED: bool = True
    COLLECTOR_GALLERY_DL_ENABLED: bool = True
    COLLECTOR_PLAYWRIGHT_ENABLED: bool = True

    COLLECTOR_TIMEOUT_SECONDS: float = 12.0
    OVERALL_ACQUISITION_TIMEOUT_SECONDS: float = 25.0
    MAX_CONCURRENT_COLLECTORS: int = 3

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
