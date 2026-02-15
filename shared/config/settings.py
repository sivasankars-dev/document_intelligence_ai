from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    PROJECT_NAME: str = "Life Admin AI"
    ENVIRONMENT: str = "development"

    DATABASE_URL: str
    REDIS_URL: str = "redis://localhost:6379/0"

    OPENAI_API_KEY: str

    CHROMA_DIR: str = "./chroma_db"
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_SECURE: bool = False
    MINIO_BUCKET: str = "documents"
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


settings = Settings()
