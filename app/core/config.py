from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env", 
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Mongo
    DATABASE_URL: str                       

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT
    JWT_SECRET: str
    JWT_ALG: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24 * 7
    JWT_ALGORITHM:str

    # Gemini
    GEMINI_API_KEY: str
    GEMINI_EMBED_MODEL: str = "models/text-embedding-004"
    GEMINI_CHAT_MODEL: str = "gemini-2.5-flash"

    # Qdrant
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: str = ""

    # Google OAuth
    GOOGLE_CLIENT_ID: str = ""
    
    MAX_FILE_MB:int = 10 * 1024 * 1024

    # Uploads
    UPLOAD_DIR: str = "uploads"
    ALLOWED_EXTENSION: list[str] = [".pdf", ".txt"]
    MAX_UPLOAD_MB: int = 10

    # RAG
    EMBED_BATCH: int = 100
    CHUNK_TOKENS: int = 512
    CHUNK_OVERLAP: int = 64

settings = Settings()