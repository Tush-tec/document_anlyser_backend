import os
import uuid

from qdrant_client import AsyncQdrantClient, models  
from service.embedder import vector_size
from core.config import settings

COLLECTION =  settings.QDRANT_COLLECTION

client = AsyncQdrantClient(
    url=settings.QDRANT_URL,
    api_key=settings.QDRANT_API_KEY,
)


def _doc_filter(doc_id: str, user_id: str | None = None) -> models.Filter:
    must = [models.FieldCondition(key="doc_id", match=models.MatchValue(value=doc_id))]
    if user_id:
        must.append(models.FieldCondition(key="user_id", match=models.MatchValue(value=user_id)))
    return models.Filter(must=must)


async def ensure_collection() -> None:
    """Call once at app startup."""
    if await client.collection_exists(COLLECTION):
        return
    await client.create_collection(
        COLLECTION,
        vectors_config=models.VectorParams(size=vector_size(), distance=models.Distance.COSINE),
    )
    # without these indexes, filtering by doc_id gets slow as data grows
    await client.create_payload_index(COLLECTION, "doc_id", models.PayloadSchemaType.KEYWORD)
    await client.create_payload_index(COLLECTION, "user_id", models.PayloadSchemaType.KEYWORD)


async def upsert_chunks(chunks: list[dict], vectors: list[list[float]]) -> None:
    """chunks: [{doc_id, user_id, page, chunk_index, text}, ...]"""
    points = [
        models.PointStruct(
            # same doc + chunk_index -> same id, so re-ingesting overwrites instead of duplicating
            id=str(uuid.uuid5(uuid.NAMESPACE_URL, f"{c['doc_id']}:{c['chunk_index']}")),
            vector=vector,
            payload=c,
        )
        for c, vector in zip(chunks, vectors)
    ]
    await client.upsert(COLLECTION, points=points, wait=True)


async def search(query_vector: list[float], doc_id: str,
                 user_id: str | None = None, top_k: int = 15) -> list[dict]:
    """The doc_id filter is what keeps a chat inside ONE document."""
    result = await client.query_points(
        COLLECTION,
        query=query_vector,
        query_filter=_doc_filter(doc_id, user_id),
        limit=top_k,
        with_payload=True,
    )
    return [{"id": p.id, "score": p.score, **p.payload} for p in result.points]


async def delete_by_doc(doc_id: str) -> None:
    await client.delete(
        COLLECTION,
        points_selector=models.FilterSelector(filter=_doc_filter(doc_id)),
    )
