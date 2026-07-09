"""Application configuration loaded once from environment variables."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Immutable-by-convention runtime settings."""

    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com/v1"
    MODEL_FLASH: str = "deepseek-v4-flash"
    MODEL_PRO: str = "deepseek-v4-pro"

    TEMPERATURE: float = 0.7
    TOP_P: float = 0.9
    MAX_TOKENS: int = 2048
    PROMPT_VERSION: str = "2026-06-25"
    QUESTION_SCHEMA_VERSION: str = "question-schema-v1"

    MEMORY_CACHE_TTL: int = 300
    MEMORY_CACHE_MAXSIZE: int = 1000
    QUESTION_SESSION_TTL: int = 1800

    VECTOR_DB_PATH: str = str(Path("data/vector_db").absolute())
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50
    RETRIEVAL_TOP_K: int = 5
    APP_DB_PATH: str = str(Path("data/app.sqlite3").absolute())

    SEARXNG_URL: str = ""
    SEARCH_TIMEOUT_SECONDS: int = 20

    SKILL_DIR: str = "app/skills"
    SKILL_WHITELIST: list[str] = ["app/skills"]
    AUTO_OPTIMIZE_THRESHOLD: int = 10

    EDGE_PATH: str = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
