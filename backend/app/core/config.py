from pathlib import Path
from typing import List, Literal, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Locate root directory and backend directory robustly
_CURRENT_DIR = Path(__file__).resolve().parent
_BACKEND_DIR = _CURRENT_DIR.parent.parent  # backend/
_ROOT_DIR = _BACKEND_DIR.parent           # project root /

_ENV_FILES = [
    str(_BACKEND_DIR / ".env"),
    str(_ROOT_DIR / ".env"),
    ".env",
]


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

    # Database Configuration
    DATABASE_BACKEND: Literal["postgresql", "sqlite"] = "postgresql"
    SUPABASE_DATABASE_URL: Optional[str] = None
    DATABASE_URL: Optional[str] = None
    DATABASE_SQLITE_PATH: str = "socialguard.db"
    DATABASE_SSL_MODE: str = "prefer"
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10
    DATABASE_REQUIRE_POSTGRES: bool = False

    # OpenRouter LLM Configuration
    OPENROUTER_ENABLED: bool = True
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_MODEL: str = "nvidia/nemotron-3.5-lightning"
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    OPENROUTER_TIMEOUT_SECONDS: float = 15.0
    OPENROUTER_MAX_TOKENS: int = 600
    OPENROUTER_TEMPERATURE: float = 0.2

    model_config = SettingsConfigDict(
        env_file=_ENV_FILES,
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    def get_effective_database_url(self) -> str:
        """
        Determines the authoritative database connection URL:
        1. If DATABASE_BACKEND is 'sqlite', resolves a fixed path relative to project root.
        2. If SUPABASE_DATABASE_URL is provided, prioritizes it (protects against ambient global DATABASE_URL overrides).
        3. Falls back to DATABASE_URL from .env or environment.
        """
        if self.DATABASE_BACKEND == "sqlite":
            db_path = (_ROOT_DIR / self.DATABASE_SQLITE_PATH).resolve()
            return f"sqlite:///{db_path}"

        # Check explicit project-scoped Supabase URL first
        target_url = self.SUPABASE_DATABASE_URL or self.DATABASE_URL

        # Read directly from project .env if environment variable was overridden by ambient system variable
        if not target_url or "localhost:5432" in target_url:
            for env_path in [(_BACKEND_DIR / ".env"), (_ROOT_DIR / ".env")]:
                if env_path.exists():
                    with open(env_path, "r", encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            if line.startswith("SUPABASE_DATABASE_URL="):
                                val = line.split("=", 1)[1].strip().strip('"').strip("'")
                                if val:
                                    target_url = val
                                    break
                            elif line.startswith("DATABASE_URL="):
                                val = line.split("=", 1)[1].strip().strip('"').strip("'")
                                if val and "localhost" not in val:
                                    target_url = val
                                    break
                if target_url and "localhost" not in target_url:
                    break

        if not target_url:
            raise ValueError(
                "DATABASE_BACKEND is set to 'postgresql' but neither SUPABASE_DATABASE_URL nor a valid DATABASE_URL is configured."
            )

        if not (target_url.startswith("postgresql://") or target_url.startswith("postgresql+")):
            raise ValueError(
                f"DATABASE_BACKEND is 'postgresql' but database scheme is not PostgreSQL: {target_url.split('://')[0]}://"
            )

        return target_url


settings = Settings()


