from fastapi import UploadFile, File, HTTPException , BackgroundTasks
import os
import uuid
from core.config import settings
from service.doc_parser import extract_text
from schemas.document import Document
from core.db import documents_collection, page_collection
from pymongo.errors import OperationFailure
import hashlib
from service import ingest
from schemas.page import Page
from service.doc_parser import extract_text
import traceback


def upload_document(user_id: str, file: UploadFile) -> dict:
    ext = os.path.splitext(file.filename)[1].lower()
    base_name = os.path.splitext(file.filename)[0]

    if ext not in settings.ALLOWED_EXTENSION:
        raise HTTPException(400, "Only .pdf and .txt are accepted")

    content = file.file.read()
    if len(content) / (1024 * 1024) > settings.MAX_FILE_MB:
        raise HTTPException(400, f"File too large. Max {settings.MAX_FILE_MB} MB.")

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    unique_name = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(settings.UPLOAD_DIR, unique_name)

    try:
        with open(file_path, "wb") as f:
            f.write(content)
    except OSError as exc:
        traceback.print_exc()
        raise HTTPException(500, f"Failed to save file: {exc}") from exc

    # ---------- parse ----------
    try:
        parse = extract_text(file_path)
    except Exception as exc:
        traceback.print_exc()
        _safe_delete(file_path)
        raise HTTPException(400, f"Failed to parse file: {exc}") from exc

    if not isinstance(parse, dict):
        _safe_delete(file_path)
        raise HTTPException(500, "Parser returned unexpected format.")

    text       = parse.get("text", "")
    pages      = parse.get("pages") or []
    page_count = parse.get("page_count", len(pages))
    word_count = parse.get("word_count", 0)

    if not pages:
        _safe_delete(file_path)
        raise HTTPException(400, "Parser extracted no pages.")
    if word_count == 0:
        _safe_delete(file_path)
        raise HTTPException(400, "No text found. Scanned PDFs need OCR.")

    # ---------- insert document ----------
    document_data = Document(
        filename=unique_name,
        
        user_id=user_id,
        original_name=file.filename,
        title=base_name,
        page_count=page_count,
        word_count=word_count,
        size_bytes=len(content),
        status="ready",
        sha256=hashlib.sha256(content).hexdigest(),
    )

    try:
        result = documents_collection.insert_one(
            document_data.model_dump(exclude={"id"})
        )
    except Exception as exc:
        traceback.print_exc()
        _safe_delete(file_path)
        raise HTTPException(500, f"Failed to insert document: {exc}") from exc

    doc_id = str(result.inserted_id)
    document_data.id = doc_id

    # ---------- insert pages in batches, rollback on failure ----------
    try:
        _insert_pages_in_batches(doc_id, user_id, pages)
    except Exception as exc:
        traceback.print_exc()
        try:
            documents_collection.delete_one({"_id": result.inserted_id})
        except Exception:
            traceback.print_exc()
        try:
            page_collection.delete_many({"doc_id": doc_id})
        except Exception:
            traceback.print_exc()
        _safe_delete(file_path)
        raise HTTPException(500, f"Failed to save pages: {exc}") from exc

    return {
        "message": "File uploaded and processed successfully",
        "id": doc_id,
        "filename": unique_name,
        "page_count": page_count,
        "word_count": word_count,
    }


def _insert_pages_in_batches(doc_id: str, user_id: str, pages: list[tuple[int, str]]) -> None:
    batch: list[dict] = []

    for page_number, page_text in pages:
        batch.append(
            Page(
                doc_id=doc_id,
                user_id=user_id,
                page_number=page_number,
                text_content=page_text,
                word_count=len(page_text.split()),
            ).model_dump(exclude={"id"})
        )

        if len(batch) >= settings.PAGE_INSERT_BATCH:
            page_collection.insert_many(batch, ordered=True)
            batch = []

    if batch:
        page_collection.insert_many(batch, ordered=True)


def _safe_delete(path: str) -> None:
    try:
        if os.path.exists(path):
            os.remove(path)
    except OSError:
        traceback.print_exc()

    
    
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
        doc = documents_collection.find_one(
            {"slug": doc_slug},
        )
        if not doc:
            return None
        return Document.from_mongo(doc)
    except OperationFailure  as err:
        
        raise HTTPException(
            status_code=500,
            detail= err.details
        ) from err
        
        
