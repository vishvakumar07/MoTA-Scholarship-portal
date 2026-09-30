"""
Application configuration.

All settings are loaded from environment variables.
Pydantic-settings validates and provides defaults.

NEVER set secrets in this file. Use .env (local) or container environment variables.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    #  -  - - Application  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  - -
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    LOG_LEVEL: str = "INFO"
    API_BASE_URL: str = "http://localhost:8000"
    CORS_ORIGINS: str = "http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    #  -  - - Database  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  - -
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10

    #  -  - - Redis  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  - -
    REDIS_URL: str = "redis://localhost:6379/0"

    #  -  - - JWT Authentication  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  - -
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    #  -  - - Field-Level Encryption  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  - -
    # Base64-encoded 32-byte key for AES-256-GCM
    # Used for: bank account numbers
    FIELD_ENCRYPTION_KEY: str

    #  -  - - Storage  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  - -
    STORAGE_PROVIDER: Literal["local", "s3"] = "local"
    LOCAL_STORAGE_PATH: str = "./storage"
    MAX_DOCUMENT_SIZE_MB: int = 10
    MAX_DOCUMENTS_PER_APPLICATION: int = 20

    # S3 (optional  -  only required when STORAGE_PROVIDER=s3)
    S3_ENDPOINT_URL: str | None = None
    S3_ACCESS_KEY_ID: str | None = None
    S3_SECRET_ACCESS_KEY: str | None = None
    S3_BUCKET_NAME: str | None = None
    S3_REGION: str = "ap-south-1"
    S3_PRESIGNED_URL_EXPIRE_SECONDS: int = 900

    #  -  - - AI Provider  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  - -
    AI_PROVIDER: Literal["gemini", "mock"] = "mock"
    GOOGLE_AI_API_KEY: str | None = None

    #  -  - - OCR Provider  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  - -
    OCR_PROVIDER: Literal["google_vision", "unavailable"] = "unavailable"
    GOOGLE_CLOUD_VISION_API_KEY: str | None = None

    #  -  - - ClamAV  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  - -
    CLAMAV_HOST: str = "clamav"
    CLAMAV_PORT: int = 3310

    #  -  - - Notifications  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  - -
    # Email (optional)
    SMTP_HOST: str | None = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_FROM_EMAIL: str = "noreply@mota-sih.local"
    SMTP_FROM_NAME: str = "MoTA Scholarship System"
    SMTP_TLS: bool = True

    @property
    def email_configured(self) -> bool:
        return bool(self.SMTP_HOST and self.SMTP_USERNAME)

    #  -  - - Government Integrations  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  - -
    AADHAAR_INTEGRATION: Literal["stub", "live"] = "stub"
    DIGILOCKER_INTEGRATION: Literal["stub", "live"] = "stub"
    DBT_INTEGRATION: Literal["stub", "live"] = "stub"
    NSP_INTEGRATION: Literal["stub", "live"] = "stub"
    MOTA_DASHBOARD_INTEGRATION: Literal["stub", "live"] = "stub"

    #  -  - - Validators  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  - -
    @field_validator("AI_PROVIDER")
    @classmethod
    def validate_ai_provider(cls, v: str, info) -> str:
        return v

    @model_validator(mode="after")
    def check_s3_config(self) -> "Settings":
        if self.STORAGE_PROVIDER == "s3":
            missing = [
                f
                for f in ["S3_ENDPOINT_URL", "S3_ACCESS_KEY_ID", "S3_SECRET_ACCESS_KEY", "S3_BUCKET_NAME"]
                if not getattr(self, f)
            ]
            if missing:
                raise ValueError(
                    f"STORAGE_PROVIDER=s3 requires these environment variables: {missing}"
                )
        return self

    @model_validator(mode="after")
    def resolve_ai_provider(self) -> "Settings":
        """Auto-downgrade AI provider to mock if API key is missing."""
        if self.AI_PROVIDER == "gemini" and not self.GOOGLE_AI_API_KEY:
            import warnings
            warnings.warn(
                "AI_PROVIDER=gemini but GOOGLE_AI_API_KEY is not set. "
                "Falling back to MockAIService. Set GOOGLE_AI_API_KEY to enable real AI.",
                stacklevel=2,
            )
            object.__setattr__(self, "AI_PROVIDER", "mock")
        return self

    @model_validator(mode="after")
    def resolve_ocr_provider(self) -> "Settings":
        """Auto-downgrade OCR provider to unavailable if API key is missing."""
        if self.OCR_PROVIDER == "google_vision" and not self.GOOGLE_CLOUD_VISION_API_KEY:
            import warnings
            warnings.warn(
                "OCR_PROVIDER=google_vision but GOOGLE_CLOUD_VISION_API_KEY is not set. "
                "Falling back to UnavailableOCR. Set GOOGLE_CLOUD_VISION_API_KEY to enable OCR.",
                stacklevel=2,
            )
            object.__setattr__(self, "OCR_PROVIDER", "unavailable")
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached settings instance. Use as FastAPI dependency."""
    return Settings()


# Module-level settings instance for non-dependency usage (e.g., Celery config)
settings = get_settings()

