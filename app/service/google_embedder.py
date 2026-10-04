import os
from functools import lru_cache

from google import genai
from google.genai import types
from core.config import settings


@lru_cache(maxsize=1)
def _client() -> genai.Client:
    """Create the Gemini client once."""
    return genai.Client(api_key=settings.GEMINI_API_KEY)


def vector_size() -> int:
    """The Qdrant collection must match this dimension.
    gemini-embedding-001 defaults to 3072 dimensions; to save storage,
    explicitly set output_dimensionality to 1536 or 768.
    """
    return 1536  # Must match the output_dimensionality below


def embed_batch(texts: list[str]) -> list[list[float]]:
    """Batch embeddings, for document ingestion.
    Synchronous call; use asyncio.to_thread() from async code.
    """
    response = _client().models.embed_content(
        model=settings.GEMINI_EMBED_MODEL,  # Should be gemini-embedding-001
        contents=texts,
        config=types.EmbedContentConfig(
            task_type="RETRIEVAL_DOCUMENT",
            output_dimensionality=1536,
        ),
    )
    return [emb.values for emb in response.embeddings]


def embed_query(text: str) -> list[float]:
    """Single embedding, for user chat queries.
    Note: task_type must be different from document ingestion.
    """
    response = _client().models.embed_content(
        model=settings.GEMINI_EMBED_MODEL,
        contents=text,
        config=types.EmbedContentConfig(
            task_type="RETRIEVAL_QUERY",
            output_dimensionality=1536,
        ),
    )
    return response.embeddings[0].values