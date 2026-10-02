from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.core.deps import get_current_user
from app.models.models import User, Document, Query as QueryRow
from app.schemas.query import QueryIn, QueryOut
from app.services.retriever import hybrid_retrieve
from app.services.reranker import rerank
from app.services import qa, validator, trust

router = APIRouter()

@router.post("/documents/{doc_id}/query", response_model=QueryOut)
def query_doc(
    doc_id: str,
    body: QueryIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    doc = db.get(Document, doc_id)
    if not doc or doc.user_id != user.id:
        raise HTTPException(404, "not found")
    if doc.status != "ready":
        raise HTTPException(409, f"document not ready (status={doc.status})")

    retrieved = hybrid_retrieve(db, user.id, doc_id, body.question, top_k=12)
    if not retrieved:
        retrieved = []
    top = rerank(body.question, retrieved, keep=5)

    if not top:
        answer_text, cits, confidence, coverage, latency = (
            validator.REFUSAL, [], "insufficient", 0.0, 0,
        )
    else:
        answer_text, cits, confidence, latency = qa.answer(body.question, top)
        answer_text, cits, confidence, coverage = validator.validate_and_repair(
            answer_text, cits, top
        )

    avg_rerank = sum(c.get("rrf", 0) for c in top) / len(top) if top else 0.0
    avg_rerank = min(1.0, avg_rerank * 3)
    score = trust.compute(coverage, avg_rerank, confidence, latency)

    row = QueryRow(
        user_id=user.id, document_id=doc_id,
        question=body.question, answer=answer_text,
        citations=[c.model_dump() for c in cits],
        trust_score=score, latency_ms=latency, model=qa.settings.GEMINI_CHAT_MODEL,
    )
    db.add(row); db.commit(); db.refresh(row)

    return QueryOut(
        query_id=row.id, answer=answer_text,
        citations=cits, trust_score=score, confidence=confidence,
    )