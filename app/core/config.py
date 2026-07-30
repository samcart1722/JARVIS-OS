from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "JARVIS-OS"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    REASONING_ENABLED: bool = False
    MEMORY_RETRIEVAL_ENABLED: bool = False
    MEMORY_PROMPT_CONTEXT_ENABLED: bool = False
    MEMORY_UPDATE_ENABLED: bool = False
    MEMORY_PROMPT_MAX_RECORDS: int = Field(default=5, gt=0)
    MEMORY_PROMPT_MAX_CHARACTERS: int = Field(default=2000, gt=0)
    OLLAMA_BASE_URL: str = "http://localhost:11434/api/generate"
    OLLAMA_MODELS_URL: str = "http://localhost:11434/api/tags"
    OLLAMA_MODEL: str = "llama3.2:3b"
    OLLAMA_TIMEOUT_SECONDS: int = Field(default=120, gt=0)

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
    )


settings = Settings()
