from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class Citation(BaseModel):
    chunk_id: str
    page: int
    quote: str
    # optional, add if you want them:
    # document_id: str
    # filename: str | None = None


class QueryIn(BaseModel):
    question: str = Field(min_length=1, max_length=500)
    # maybe:
    # document_id: str | None = None    # restrict to one doc
    # top_k: int = 5


class Confidence(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"


class QueryOut(BaseModel):
    query_id: str
    question: str
    answer: str
    citations: list[Citation]
    trust_score: float = Field(ge=0.0, le=1.0)
    confidence: Confidence
    model: str | None = None
    created_at: datetime | None = None

    @classmethod
    def from_mongo(cls, doc: dict, confidence_fn) -> "QueryOut":
        doc = dict(doc)
        return cls(
            query_id=str(doc.pop("_id")),
            question=doc["question"],
            answer=doc["answer"],
            citations=[Citation(**c) for c in doc.get("citations", [])],
            trust_score=doc["trust_score"],
            confidence=confidence_fn(doc["trust_score"]),
            model=doc.get("model"),
            created_at=doc.get("created_at"),
        )