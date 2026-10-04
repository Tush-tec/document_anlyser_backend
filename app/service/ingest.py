"""Background ingestion: parse -> pages (Mongo) -> chunks -> Gemini vectors -> Qdrant.

It is a plain `def`, so FastAPI runs it in a worker thread and the event loop stays free.
Every outcome is written to the document row, so nothing fails silently:
    queued -> processing (stage: parsing / saving_pages / embedding) -> ready | failed (+ error)
"""
import logging
from datetime import datetime, timedelta

from bson import ObjectId

from core.config import settings
from core.db import documents_collection, page_collection
from schemas.page import Page
from service import chunker, embedder, vector_store
from service.doc_parser import extract_text

log = logging.getLogger(__name__)


def _set(doc_id: str, **fields) -> None:
    documents_collection.update_one({"_id": ObjectId(doc_id)}, {"$set": fields})


def ingest_document(doc_id: str, user_id: str, file_path: str) -> None:
    try:
        _set(doc_id, status="processing", stage="parsing", error=None)
        _clear_derived_data(doc_id)                      # safe to re-run

        # ---- 1. parse ---------------------------------------------------------
        parse = extract_text(file_path)
        pages = parse.get("pages") or []
        word_count = parse.get("word_count", 0)
        if not pages:
            raise ValueError("Parser extracted no pages.")
        if len(pages) > settings.MAX_PAGES:
            raise ValueError(f"Document has {len(pages)} pages; the limit is {settings.MAX_PAGES}.")
        if word_count == 0:
            raise ValueError("No text found. Scanned PDFs need OCR.")

        # ---- 2. pages -> Mongo ------------------------------------------------
        _set(doc_id, stage="saving_pages", page_count=len(pages), word_count=word_count)
        _insert_pages(doc_id, user_id, pages)

        # ---- 3. pages -> chunks -> vectors -> Qdrant --------------------------
        _set(doc_id, stage="embedding", chunks_done=0)
        chunk_count = _chunk_and_embed(doc_id, user_id)

        _set(doc_id, status="ready", stage="done",
             chunk_count=chunk_count, ready_at=datetime.utcnow())

    except Exception as exc:
        log.exception("Ingestion failed for document %s", doc_id)
        try:
            _set(doc_id, status="failed", stage="failed", error=str(exc)[:500])
        except Exception:
            import traceback
            traceback.print_exc()          
            log.exception("Could not record failure for document %s", doc_id)
        _clear_derived_data(doc_id)                      # rollback pages + vectors


def _insert_pages(doc_id: str, user_id: str, pages: list[tuple[int, str]]) -> None:
    batch: list[dict] = []
    for page_number, page_text in pages:
        batch.append(Page(
            doc_id=doc_id, user_id=user_id, page_number=page_number,
            text_content=page_text, word_count=len(page_text.split()),
        ).model_dump(exclude={"id"}))

        if len(batch) >= settings.PAGE_INSERT_BATCH:
            page_collection.insert_many(batch, ordered=False)
            batch = []
    if batch:
        page_collection.insert_many(batch, ordered=False)


def _chunk_and_embed(doc_id: str, user_id: str) -> int:
    batch: list[dict] = []
    chunk_index = 0

    # stream pages from Mongo in order; never load the whole document at once
    cursor = page_collection.find(
        {"doc_id": doc_id}, {"page_number": 1, "text_content": 1}
    ).sort("page_number", 1)

    for page in cursor:
        for piece in chunker.chunk_page(page["text_content"], page["page_number"]):
            batch.append({
                "doc_id": doc_id,
                "user_id": user_id,
                "page": piece["page"],
                "chunk_index": chunk_index,
                "text": piece["text"],
            })
            chunk_index += 1

            if len(batch) >= settings.EMBED_BATCH:
                _flush(doc_id, batch, chunk_index)
                batch = []
    if batch:
        _flush(doc_id, batch, chunk_index)

    return chunk_index


def _flush(doc_id: str, batch: list[dict], chunks_done: int) -> None:
    vectors = embedder.embed_batch([c["text"] for c in batch])
    vector_store.upsert_chunks_sync(batch, vectors)
    _set(doc_id, chunks_done=chunks_done)                # progress for the UI


def _clear_derived_data(doc_id: str) -> None:
    """Delete pages and vectors of a document. Never raises."""
    try:
        page_collection.delete_many({"doc_id": doc_id})
    except Exception:
        log.exception("Could not delete pages for %s", doc_id)
    try:
        vector_store.delete_by_doc_sync(doc_id)
    except Exception:
        log.exception("Could not delete vectors for %s", doc_id)


def recover_stuck_documents(max_age_minutes: int = 60) -> int:
    """Call at startup. Background tasks die with the server process, so documents left in
    queued/processing for too long would stay stuck forever; mark them failed instead."""
    cutoff = datetime.utcnow() - timedelta(minutes=max_age_minutes)
    result = documents_collection.update_many(
        {"status": {"$in": ["queued", "processing"]}, "created_at": {"$lt": cutoff}},
        {"$set": {"status": "failed", "stage": "failed",
                  "error": "Processing was interrupted. Please upload the document again."}},
    )
    return result.modified_count
