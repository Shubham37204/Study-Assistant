from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_FILE = Path(__file__).resolve().parent / ".env"

class Settings(BaseSettings):
    groq_api_key: str = Field(..., min_length=1)
    llm_model_fast: str = "llama-3.1-8b-instant"
    llm_model_quality: str = "llama-3.3-70b-versatile"
    embed_model: str = "BAAI/bge-small-en-v1.5"
    embed_batch_size: int = Field(default=32, ge=1, le=256)
    chunk_size: int = Field(default=1800, ge=200)
    chunk_overlap: int = Field(default=150, ge=0)
    chroma_path: str = "./chroma_db"
    bm25_path: str = "./bm25_index"
    database_url: str = "sqlite:///./study_assistant.db"
    upload_dir: str = "./uploads"
    max_upload_bytes: int = 50 * 1024 * 1024
    allowed_extensions: list[str] = Field(
        default_factory=lambda: [".pdf", ".txt", ".md", ".png", ".jpg", ".jpeg", ".webp"]
    )
    critic_max_retries: int = Field(default=2, ge=0, le=5)
    retrieval_top_k: int = Field(default=5, ge=1, le=20)
    retrieval_fetch_k: int = Field(default=20, ge=5, le=100)
    clerk_secret_key: str | None = None  

    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

settings = Settings()
