from __future__ import annotations

from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_FILE = Path(__file__).resolve().parent / ".env"

class Settings(BaseSettings):
    groq_api_key: str = Field(..., min_length=1)
    llm_model_fast: str = "llama-3.1-8b-instant"
    llm_model_quality: str = "llama-3.3-70b-versatile"
    embed_model: str = "BAAI/bge-small-en-v1.5"
    embed_batch_size: int = Field(default=32, ge=1)
    chunk_size: int = Field(default=1800, ge=200)
    chunk_overlap: int = Field(default=150, ge=0)

    database_url: str = "sqlite:///./study_assistant.db"

    redis_url: str = "redis://localhost:6379/0"

    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"
    celery_always_eager: bool = False

    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str | None = None  
    qdrant_collection: str = "study_assistant"
    embed_size: int = 384

    bm25_path: str = "./bm25_index"
    upload_dir: str = "./uploads"
    max_upload_bytes: int = 50 * 1024 * 1024
    allowed_extensions: list[str] = Field(
        default_factory=lambda: [".pdf", ".txt", ".md", ".png", ".jpg", ".jpeg", ".webp"]
    )

    query_cache_ttl: int = 3600
    critic_max_retries: int = Field(default=2, ge=0)
    retrieval_top_k: int = Field(default=5, ge=1)
    retrieval_fetch_k: int = Field(default=20, ge=5)

    clerk_secret_key: str | None = None
    langchain_api_key: str | None = None
    langchain_project: str = "study-assistant"
    langchain_tracing_v2: str = "false"

    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
