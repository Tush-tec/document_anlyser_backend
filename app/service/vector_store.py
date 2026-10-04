import uuid

from qdrant_client import AsyncQdrantClient, QdrantClient, models

from core.config import settings
from service.embedder import vector_size

COLLECTION = settings.QDRANT_COLLECTION

_conn = dict(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY or None)
client = AsyncQdrantClient(**_conn)       # chat / search (async routes)
sync_client = QdrantClient(**_conn)       # background ingestion (runs in a thread)


def _doc_filter(doc_id: str, user_id: str | None = None) -> models.Filter:
    must = [models.FieldCondition(key="doc_id", match=models.MatchValue(value=doc_id))]
    if user_id:
        must.append(models.FieldCondition(key="user_id", match=models.MatchValue(value=user_id)))
    return models.Filter(must=must)


def _points(chunks: list[dict], vectors: list[list[float]]) -> list[models.PointStruct]:
    return [
        models.PointStruct(
            # same doc + chunk_index -> same id, so re-ingesting overwrites instead of duplicating
            id=str(uuid.uuid5(uuid.NAMESPACE_URL, f"{c['doc_id']}:{c['chunk_index']}")),
            vector=vector,
            payload=c,
        )
        for c, vector in zip(chunks, vectors)
    ]


# ---------------- startup + ingestion (sync) ----------------
def ensure_collection_sync() -> None:
    """Call once at app startup."""
    if sync_client.collection_exists(COLLECTION):
        return
    sync_client.create_collection(
        COLLECTION,
        vectors_config=models.VectorParams(size=vector_size(), distance=models.Distance.COSINE),
    )
    # without these indexes, filtering by doc_id gets slow as data grows
    sync_client.create_payload_index(COLLECTION, "doc_id", models.PayloadSchemaType.KEYWORD)
    sync_client.create_payload_index(COLLECTION, "user_id", models.PayloadSchemaType.KEYWORD)


def upsert_chunks_sync(chunks: list[dict], vectors: list[list[float]]) -> None:
    """chunks: [{doc_id, user_id, page, chunk_index, text}, ...]"""
    sync_client.upsert(COLLECTION, points=_points(chunks, vectors), wait=True)


def delete_by_doc_sync(doc_id: str) -> None:
    sync_client.delete(
        COLLECTION,
        points_selector=models.FilterSelector(filter=_doc_filter(doc_id)),
    )


# ---------------- chat (async) ----------------
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
