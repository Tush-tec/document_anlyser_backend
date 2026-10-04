from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, BackgroundTasks
from controller import document_controller
from schemas.document import  Document
from typing import List
from schemas.response import APIResponse
from service.dependencies import auth_middleware
from core.db  import documents_collection

router = APIRouter(prefix="/documents", tags=["document"])

@router.post("/upload")
def upload_document(
    file: UploadFile = File(...),
    user: dict = Depends(auth_middleware),
):
    return  document_controller.upload_document(
        user_id=user["id"],    
        file=file,
    )


@router.get("/", response_model=APIResponse[List[Document]])
async def get_documents():
    docs = await document_controller.get_documents()
    return {
        "status_code": 200,
        "message": "Documents fetched successfully",
        "data": docs,
    }
    
@router.get("/user-docs", response_model=APIResponse[List[Document]])
async def user_docs(user: dict =  Depends(auth_middleware)):
    doc = await document_controller.find_user_docs(user)
    
    return {
        "status_code": 200,
        "message": "Document fetched successfully",
        "data": doc,   
    }

@router.get("/{doc_slug}", response_model=APIResponse[Document])
async def get_particular_docs(doc_slug: str):
    doc = await document_controller.find_particular_document(doc_slug)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return {
        "status_code": 200,
        "message": "Document fetched successfully",
        "data": doc,
    }
    
