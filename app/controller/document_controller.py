from fastapi import APIRouter, UploadFile, File, HTTPException
import os
import uuid
from core.config import settings
from service.doc_parser import extract_text
from schemas.document import Document
from core.db import documents_collection

async def upload_document(user_id:str, file : UploadFile = File(...)):
    """
    upload a PDF or TXT% contract for analysis
    """
    
    print("===== file v======= 14", file)
    
    ext = os.path.splitext(file.filename)[1].lower()
     
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
    print("PARSER RETURNED:", parse)
    
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
        text_content=text,
        page_count=page_count,
        word_count=word_count,
        size_bytes=len(content),
        # sha256=hashlib.sha256(content).hexdigest(),
    )

    
    doc = contract_data.model_dump()
    result = documents_collection.insert_one(doc)
    doc.pop("_id", None)
    contract_data.id = str(result.inserted_id)
    return {
        "message": "File uploaded and processed successfully",
        "contract": contract_data.model_dump(),   # cleaner: dump from the model, not the raw doc
        "id": contract_data.id,
    }
    
    
async def get_documents():
    cursor = documents_collection.find({}).sort([("created_at", -1)])
    return [Document.from_mongo(doc).model_dump() for doc in cursor]
    