import os
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./data/insyvera.db")
    data_dir: Path = Path(os.getenv("DATA_DIR", "./data"))
    redis_url: str = os.getenv("REDIS_URL", "")
    storage: str = os.getenv("STORAGE_BACKEND", "local")
    s3_endpoint: str = os.getenv("S3_ENDPOINT", "http://localhost:9000")
    s3_access: str = os.getenv("MINIO_ROOT_USER", "insyvera")
    s3_secret: str = os.getenv("MINIO_ROOT_PASSWORD", "")
    bucket: str = os.getenv("S3_BUCKET", "insyvera")
    eager: bool = os.getenv("TASK_ALWAYS_EAGER", "true").lower() == "true"
    secure_cookie: bool = os.getenv("COOKIE_SECURE", "false").lower() == "true"
    origins: str = os.getenv("ALLOWED_ORIGINS", "http://localhost:5180,http://127.0.0.1:5180,http://localhost:8100,http://127.0.0.1:8100")
    provider: str = os.getenv("MODEL_PROVIDER", "extractive")
    model: str = os.getenv("MODEL_ID", "qwen3:8b")
    ollama: str = os.getenv("OLLAMA_URL", "http://localhost:11434")
    embedding_provider: str = os.getenv("EMBEDDING_PROVIDER", "lexical")
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
    dimensions: int = int(os.getenv("EMBEDDING_DIMENSIONS", "768"))
    openai_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_url: str = os.getenv("OPENAI_URL", "https://api.openai.com/v1")
    external_web: bool = os.getenv("ALLOW_EXTERNAL_WEB", "false").lower() == "true"
    max_upload: int = 20 * 1024 * 1024
    max_cells: int = 200000
    max_chunks: int = 10000
    session_hours: int = 72

settings = Settings()
settings.data_dir.mkdir(parents=True, exist_ok=True)
