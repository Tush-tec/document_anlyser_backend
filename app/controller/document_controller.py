from fastapi import UploadFile, File, HTTPException, BackgroundTasks
import os
import uuid
from core.config import settings
from service.doc_parser import extract_text
from schemas.document import Document
from core.db import documents_collection
from pymongo.errors import OperationFailure
import hashlib
from service import ingest

async def upload_document(db, user_id:str, background_tasks: BackgroundTasks,  file : UploadFile = File(...), ):
    """
    upload a PDF or TXT% contract for analysis
    """
        
    ext = os.path.splitext(file.filename)[1].lower()
    base_name = os.path.splitext(file.filename)[0]
     
    if ext not in settings.ALLOWED_EXTENSION:
        raise  HTTPException(
            status_code=400,
            detail="Only .pdf and .txt are accepted"
        )
    
    content = await file.read()
    size_mb = len(content) / (1024 *  1024)
    
    if size_mb > settings.MAX_FILE_MB : 
        raise HTTPException(
            status_code=400,
            detail="File size is too large upload. we accept file only 10mb"
        )   

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    unique_name = f"{uuid.uuid4().hex}{ext}"
        
    file_path= os.path.join(settings.UPLOAD_DIR, unique_name)
    
    with open(file_path, "wb") as f:
        f.write(content)
        
        
    parse = extract_text(file_path)
    
    if isinstance(parse, dict):
        text       = parse.get("text", "")
        page_count = parse.get("page_count", parse.get("pages", 0))
        word_count = parse.get("word_count", parse.get("words", len(text.split())))
    else:
        text       = parse or ""
        page_count = 0
        word_count = len(text.split())
    
    contract_data = Document(
        filename=unique_name,
        user_id = user_id,
        original_name=file.filename,
        title =  base_name,
        page_count=page_count,
        word_count=word_count,
        size_bytes=len(content),
        status = "queued",
        sha256=hashlib.sha256(content).hexdigest(),
    )

    
    doc = contract_data.model_dump()
    result = documents_collection.insert_one(doc)
    doc.pop("_id", None)
    contract_data.id = str(result.inserted_id)
    doc_id =  str(result.inserted_id)
    
    # Run the Heavy Work after the response is sent
    background_tasks.add_task(ingest.ingest_documents, db, doc_id, str(file_path))
    
    
    return {
        "message": "File uploaded and processed successfully",
        "contract": contract_data.model_dump(),   # cleaner: dump from the model, not the raw doc
        "id": contract_data.id,
    }
    
    
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
        
        
