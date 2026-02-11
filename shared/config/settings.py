from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    PROJECT_NAME: str = "Life Admin AI"
    ENVIRONMENT: str = "development"

    DATABASE_URL: str
    REDIS_URL: str

    OPENAI_API_KEY: str

    CHROMA_DIR: str = "./chroma_db"

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True
    )


settings = Settings()
