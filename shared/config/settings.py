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
    QA_THREAD_TTL_SECONDS: int = 86400
    QA_THREAD_MAX_TURNS: int = 6
    NOTIFICATION_PREF_CACHE_TTL_SECONDS: int = 300
    AUTH_RATE_LIMIT_WINDOW_SECONDS: int = 60
    LOGIN_RATE_LIMIT_PER_WINDOW: int = 10
    REGISTER_RATE_LIMIT_PER_WINDOW: int = 5

    OPENAI_API_KEY: str

    CHROMA_DIR: str = "./chroma_db"
    GCS_BUCKET: str = "documents"
    GCP_PROJECT_ID: str | None = None
    GCS_CREDENTIALS_FILE: str | None = None
    GCS_CREDENTIALS_JSON: str | None = None
    MAX_UPLOAD_SIZE_MB: int = 20
    ALLOWED_UPLOAD_CONTENT_TYPES: str = (
        "application/pdf,"
        "text/plain,"
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document,"
        "text/csv,"
        "application/vnd.ms-excel,"
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,"
        "image/jpeg,"
        "image/png,"
        "message/rfc822,"
        "application/vnd.ms-outlook,"
        "text/html"
    )
    ALLOWED_UPLOAD_EXTENSIONS: str = ".pdf,.txt,.docx,.csv,.xlsx,.xls,.jpg,.jpeg,.png,.eml,.msg,.html,.htm"
    PII_REDACTION_ENABLED: bool = True
    JWT_SECRET_KEY: str = "siva_jwt_secret_key"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    REMINDER_BATCH_SIZE: int = 50
    NOTIFICATION_DRY_RUN: bool = True
    NOTIFICATION_EMAIL_FROM: str = "noreply@example.com"
    SMTP_HOST: str | None = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_USE_TLS: bool = True
    SMS_PROVIDER_URL: str | None = None
    SMS_PROVIDER_TOKEN: str | None = None
    PUSH_PROVIDER_URL: str | None = None
    PUSH_PROVIDER_TOKEN: str | None = None
    NOTIFICATION_AUTO_RETRY: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
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

        if not self.GCS_BUCKET:
            raise ValueError("GCS_BUCKET must be configured for non-development environment")

        return self


settings = Settings()
