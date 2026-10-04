import asyncio
import os 
from datetime import datetime
from bson import ObjectId
from fastapi import FastAPI, HTTPException

from schemas.page import Page
from service import chunker, embedder, parser, vector_store
from core.db import page_collection, documents_collection
from core.config import settings

async def _set(db, doc_id: str, **fields) -> None:
    db.update_one(
        {"_id": ObjectId(doc_id)},
        {"$set": fields}
    )
    

async def _extract_to_mongo(db, doc_id, user_id, file_path) -> tuple[int, int]:
    pages = await asyncio.to_thread(parser.extract_pages, file_path) # blocking -> thread
    
    try:
        if len(pages) > settings.MAX_PAGES:
                raise ValueError(f"PDF has {len(pages)} pages; the limit is {settings.MAX_PAGES}.")
            
        batch, total_words = [], 0
        for page_number, text in pages:
                page = Page(doc_id=doc_id, user_id=user_id, page_number=page_number,
                            text=text, word_count=len(text.split()))
                total_words += page.word_count
                batch.append(page.model_dump(exclude={"id"}))
        
                if len(batch) >= settings.PAGE_INSERT_BATCH:
                    await page_collection.insert_many(batch)
                    batch = []
        if batch:
                await page_collection.insert_many(batch)
                
    except Exception as exc:
        await _set(db, doc_id, status="failed", error=str(exc))
        
        
async def _chunk_and_embed(db, doc_id, user_id) -> int:
    batch, chunk_index = [], 0

    # stream pages from Mongo in order; never load the whole document at once
    cursor = db.find({"doc_id": doc_id}).sort("page_number", 1)
    async for page in cursor:
        for piece in chunker.chunk_page(page["text"], page["page_number"]):
            batch.append({
                "doc_id": doc_id,
                "user_id": user_id,
                "page": piece["page"],
                "chunk_index": chunk_index,
                "text": piece["text"],
            })
            chunk_index += 1

            if len(batch) >= settings.EMBED_BATCH:
                await _flush(batch)
                batch = []
    if batch:
        await _flush(batch)

    return chunk_index


async def _flush(batch: list[dict]) -> None:
    texts = [c["text"] for c in batch]
    vectors = await asyncio.to_thread(embedder.embed_batch, texts)   
    await vector_store.upsert_chunks(batch, vectors)
    
    
async def ingest_documents(db, doc_id:str, file_path: str) -> None:
    """Runs in the background after upload: Queued -> Processing -> Ready/Failed"""
    
    try:
        # Find  document
        doc =  db.find_one({"_id" : ObjectId(doc_id)})
        print(f"[INGEST] find_one returned {type(doc)}", flush=True)
        
        user_id = doc.user_id
        
        await _set(db, doc_id, status="processing") 
        print("[INGEST] status=processing", flush=True)

        
        # safe to re-run: clear anything left from an earlier attempt
        await page_collection.delete_many({"doc_id": doc_id})
        print("[INGEST] cleared old pages", flush=True)
        await vector_store.delete_by_doc(doc_id)
        
        # ---- stage 1: PDF -> `pages` collection --------------------------------
        page_count, word_count =  await _extract_to_mongo(db, doc_id, user_id)
        print(f"[INGEST] extracted pages={page_count} words={word_count}", flush=True)
        if word_count == 0:
            raise ValueError("No text found in this PDF. Scanned PDFs need OCR.")
        await _set(db, doc_id, page_count=page_count, word_count=word_count)
        
         # ---- stage 2: `pages` -> chunks -> vectors -> Qdrant ---------------------
        chunk_count = await _chunk_and_embed(db, doc_id, user_id)
        await _set(db, doc_id, chunk_count=chunk_count,
                   status="ready", ready_at=datetime.utcnow())

    except Exception as exc:
        await _set(db, doc_id, status="failed", error=str(exc))
        try:  # best-effort cleanup of half-written data
            await vector_store.delete_by_doc(doc_id)
        except Exception:
            raise HTTPException(
                status_code=500,
                detail=exc
            )