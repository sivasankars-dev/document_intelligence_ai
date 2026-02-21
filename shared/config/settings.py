from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator


class Settings(BaseSettings):

    PROJECT_NAME: str = "Life Admin AI"
    ENVIRONMENT: str = "development"

    DATABASE_URL: str
    REDIS_URL: str = "redis://localhost:6379/0"
    CACHE_ENABLED: bool = True
    QA_RETRIEVAL_CACHE_TTL_SECONDS: int = 900
    QA_RESPONSE_CACHE_TTL_SECONDS: int = 300
    NOTIFICATION_PREF_CACHE_TTL_SECONDS: int = 300
    AUTH_RATE_LIMIT_WINDOW_SECONDS: int = 60
    LOGIN_RATE_LIMIT_PER_WINDOW: int = 10
    REGISTER_RATE_LIMIT_PER_WINDOW: int = 5

    OPENAI_API_KEY: str

    CHROMA_DIR: str = "./chroma_db"
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_SECURE: bool = False
    MINIO_BUCKET: str = "documents"
    MAX_UPLOAD_SIZE_MB: int = 20
    ALLOWED_UPLOAD_CONTENT_TYPES: str = "application/pdf,text/plain"
    ALLOWED_UPLOAD_EXTENSIONS: str = ".pdf,.txt"
    PII_REDACTION_ENABLED: bool = True
    JWT_SECRET_KEY: str = "siva_jwt_secret_key"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    REMINDER_BATCH_SIZE: int = 50

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True
    )

    @model_validator(mode="after")
    def validate_security_defaults(self):
        env = (self.ENVIRONMENT or "").strip().lower()
        if env not in {"production", "prod", "staging"}:
            return self

        weak_jwt = {
            "",
            "siva_jwt_secret_key",
            "change-this-in-production",
            "change_me",
        }
        if self.JWT_SECRET_KEY in weak_jwt or len(self.JWT_SECRET_KEY) < 32:
            raise ValueError("JWT_SECRET_KEY is weak for non-development environment")

        if self.MINIO_ACCESS_KEY == "minioadmin" or self.MINIO_SECRET_KEY == "minioadmin":
            raise ValueError("MinIO credentials must be changed for non-development environment")

        if not self.MINIO_SECURE:
            raise ValueError("MINIO_SECURE must be true for non-development environment")

        return self


settings = Settings()
