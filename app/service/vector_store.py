from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue,
)
from app.core.config import settings
from app.services.embedder import EMBED_DIM

_client = QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY or None)
COLLECTION = "chunks"

def ensure_collection():
    existing = {c.name for c in _client.get_collections().collections}
    if COLLECTION not in existing:
        _client.create_collection(
            collection_name=COLLECTION,
            vectors_config=VectorParams(size=EMBED_DIM, distance=Distance.COSINE),
        )

def upsert_chunks(user_id: str, doc_id: str, chunks, vectors):
    points = [
        PointStruct(
            id=c.id,
            vector=v,
            payload={
                "user_id": user_id,
                "doc_id": doc_id,
                "chunk_id": c.id,
                "page": c.page,
                "text": c.text,
            },
        )
        for c, v in zip(chunks, vectors)
    ]
    _client.upsert(collection_name=COLLECTION, points=points, wait=True)

def search(user_id: str, doc_id: str, query_vector: list[float], top_k: int = 20):
    flt = Filter(must=[
        FieldCondition(key="user_id", match=MatchValue(value=user_id)),
        FieldCondition(key="doc_id",  match=MatchValue(value=doc_id)),
    ])
    return _client.search(
        collection_name=COLLECTION,
        query_vector=query_vector,
        query_filter=flt,
        limit=top_k,
        with_payload=True,
    )

def delete_doc(user_id: str, doc_id: str):
    flt = Filter(must=[
        FieldCondition(key="user_id", match=MatchValue(value=user_id)),
        FieldCondition(key="doc_id",  match=MatchValue(value=doc_id)),
    ])
    _client.delete(collection_name=COLLECTION, points_selector=flt, wait=True)