from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "JARVIS-OS"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    REASONING_ENABLED: bool = False
    OLLAMA_BASE_URL: str = "http://localhost:11434/api/generate"
    OLLAMA_MODELS_URL: str = "http://localhost:11434/api/tags"
    OLLAMA_MODEL: str = "llama3.2:3b"
    OLLAMA_TIMEOUT_SECONDS: int = Field(default=120, gt=0)

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
    )


settings = Settings()
