import os
from functools import lru_cache

from sentence_transformers import SentenceTransformer  
from core.config import settings


@lru_cache(maxsize=1)
def _model() -> SentenceTransformer:
    return SentenceTransformer(settings.EMBED_MODEL_NAME)


def vector_size() -> int:
    """Qdrant collection size must equal this number."""
    return _model().get_embedding_dimension()


def embed_batch(texts: list[str]) -> list[list[float]]:
    """Input: list of strings. Output: list of vectors. No Mongo, no Qdrant here.

    Blocking (CPU heavy): call with asyncio.to_thread() from async code.
    To use Gemini embeddings instead, only this function body changes.
    """
    return _model().encode(texts, batch_size=32, normalize_embeddings=True).tolist()


def embed_query(text: str) -> list[float]:
    return embed_batch([text])[0]
