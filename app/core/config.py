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
    GEMINI_EMBED_MODEL: str = "gemini-embedding-001"
    GEMINI_CHAT_MODEL: str = "gemini-2.5-flash"
    GEMINI_BATCH_SIZE:int= 1000
    
    

    # Qdrant
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: str = ""

    # Google OAuth
    GOOGLE_CLIENT_ID: str = ""
    
    MAX_FILE_MB:int = 20 * 1024 * 1024
    MAX_PAGES: int = 2000
    PAGE_INSERT_BATCH: int = 500                         # pages per Mongo insert_many
    EMBED_BATCH:int = 64   
    EMBED_MODEL_NAME: str="all-MiniLM-L6-v2"    

    # Uploads
    UPLOAD_DIR: str = "uploads"
    ALLOWED_EXTENSION: list[str] = [".pdf", ".txt"]
    MAX_UPLOAD_MB: int = 20

    # RAG
    EMBED_BATCH: int = 100
    CHUNK_TOKENS: int = 512
    # Chunking (words, not tokens)
    CHUNK_WORDS: int = 300
    CHUNK_OVERLAP_WORDS: int = 50
    
    QDRANT_COLLECTION:str 
    QDRANT_URL:str
    QDRANT_API_KEY : str

settings = Settings()