from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # ── Application ───────────────────────────────────────────────────────────
    APP_ENV:  str = "development"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000

    # ── Database ──────────────────────────────────────────────────────────────
    DATABASE_URL: str

    # ── Redis ─────────────────────────────────────────────────────────────────
    REDIS_URL:              str = "redis://localhost:6379/0"
    CELERY_BROKER_URL:      str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND:  str = "redis://localhost:6379/2"

    # ── JWT ───────────────────────────────────────────────────────────────────
    JWT_PRIVATE_KEY_PATH:              str = "/run/secrets/jwt_private_key"
    JWT_PUBLIC_KEY_PATH:               str = "/run/secrets/jwt_public_key"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES:   int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS:     int = 7
    JWT_ALGORITHM:                     str = "RS256"

    # ── MinIO ─────────────────────────────────────────────────────────────────
    MINIO_ENDPOINT:         str = "minio:9000"
    MINIO_ACCESS_KEY:       str
    MINIO_SECRET_KEY:       str
    MINIO_EVIDENCE_BUCKET:  str = "forensic-evidence"
    MINIO_RESULTS_BUCKET:   str = "forensic-results"
    MINIO_MODELS_BUCKET:    str = "forensic-models"
    MINIO_USE_SSL:          bool = False

    # ── ML Service ────────────────────────────────────────────────────────────
    ML_SERVICE_URL:            str = "http://ml-service:8001"
    ML_REQUEST_TIMEOUT_SECONDS: int = 300

    # ── File Upload ───────────────────────────────────────────────────────────
    MAX_IMAGE_SIZE_MB: int = 50
    MAX_VIDEO_SIZE_MB: int = 2048
    ALLOWED_IMAGE_TYPES: str = "image/jpeg,image/png,image/bmp,image/tiff"
    ALLOWED_VIDEO_TYPES: str = "video/mp4,video/x-msvideo,video/quicktime"

    # ── Security ──────────────────────────────────────────────────────────────
    CORS_ORIGINS:                   str = "http://localhost:3000"
    RATE_LIMIT_LOGIN_MAX:           int = 5
    RATE_LIMIT_LOGIN_WINDOW_SECONDS: int = 600

    @property
    def allowed_mime_types(self) -> List[str]:
        return (self.ALLOWED_IMAGE_TYPES + "," + self.ALLOWED_VIDEO_TYPES).split(",")

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]

    @property
    def max_image_bytes(self) -> int:
        return self.MAX_IMAGE_SIZE_MB * 1024 * 1024

    @property
    def max_video_bytes(self) -> int:
        return self.MAX_VIDEO_SIZE_MB * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
