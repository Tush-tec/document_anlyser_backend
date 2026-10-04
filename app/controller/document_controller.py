import hashlib
import os
import traceback
import uuid

from bson import ObjectId
from fastapi import BackgroundTasks, HTTPException, UploadFile
from pymongo.errors import OperationFailure
from slugify import slugify

from core.config import settings
from core.db import documents_collection
from schemas.document import Document
from service import ingest


def upload_document(background_tasks: BackgroundTasks, user_id: str, file: UploadFile) -> dict:
    """Fast path only: validate, save the file, create the row, queue the job, return."""
    ext = os.path.splitext(file.filename)[1].lower()
    base_name = os.path.splitext(file.filename)[0]

    if ext not in settings.ALLOWED_EXTENSION:
        raise HTTPException(400, "Only .pdf and .txt are accepted")

    content = file.file.read()
    if len(content) > settings.MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(400, f"File too large. Max {settings.MAX_UPLOAD_MB} MB.")
    if ext == ".pdf" and not content.startswith(b"%PDF-"):
        raise HTTPException(400, "This file is not a valid PDF.")

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    unique_name = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(settings.UPLOAD_DIR, unique_name)

    try:
        with open(file_path, "wb") as f:
            f.write(content)
    except OSError as exc:
        traceback.print_exc()
        raise HTTPException(500, f"Failed to save file: {exc}") from exc

    document = Document(
        filename=unique_name,
        user_id=user_id,
        original_name=file.filename,
        title=base_name,
        # slug must be unique (unique index), so add part of the random file name
        slug=f"{slugify(base_name, algorithm='modern')}-{unique_name[:8]}",
        size_bytes=len(content),
        storage_key=unique_name,
        status="queued",
        stage="queued",
        sha256=hashlib.sha256(content).hexdigest(),
    )

    try:
        result = documents_collection.insert_one(document.model_dump(exclude={"id"}))
    except Exception as exc:
        traceback.print_exc()
        _safe_delete(file_path)
        raise HTTPException(500, f"Failed to insert document: {exc}") from exc

    doc_id = str(result.inserted_id)

    # the slow work (parse, pages, chunks, embeddings) runs AFTER the response is sent
    background_tasks.add_task(ingest.ingest_document, doc_id, user_id, file_path)

    return {"id": doc_id, "status": "queued", "filename": unique_name,
            "message": "Upload received. Processing started."}


def get_document_status(user_id: str, doc_id: str) -> dict:
    if not ObjectId.is_valid(doc_id):
        raise HTTPException(404, "Document not found")
    doc = documents_collection.find_one({"_id": ObjectId(doc_id), "user_id": user_id})
    if not doc:
        raise HTTPException(404, "Document not found")
    return {
        "id": doc_id,
        "status": doc["status"],
        "stage": doc.get("stage"),
        "page_count": doc.get("page_count", 0),
        "chunk_count": doc.get("chunk_count"),
        "chunks_done": doc.get("chunks_done", 0),
        "error": doc.get("error"),
        "ready_at": doc.get("ready_at"),
    }


def _safe_delete(path: str) -> None:
    try:
        if os.path.exists(path):
            os.remove(path)
    except OSError:
        traceback.print_exc()


# ---------------- unchanged from your version ----------------
async def get_documents():
    cursor = documents_collection.find({}).sort([("created_at", -1)])
    return [Document.from_mongo(doc).model_dump() for doc in cursor]


async def find_user_docs(user: dict) -> list[Document]:
    try:
        user_id = user["id"]
        docs = documents_collection.find({"user_id": user_id}).sort([("created_at", -1)])
        return [Document.from_mongo(doc) for doc in docs]
    except OperationFailure as err:
        raise HTTPException(status_code=500, detail=err.details) from err


async def find_particular_document(doc_slug: str) -> Document | None:
    try:
        doc = documents_collection.find_one({"slug": doc_slug})
        if not doc:
            return None
        return Document.from_mongo(doc)
    except OperationFailure as err:
        raise HTTPException(status_code=500, detail=err.details) from err
