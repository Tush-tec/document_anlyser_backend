from fastapi import APIRouter, UploadFile, File, Depends
from controller import document_controller
from schemas.document import  Document
from typing import List
from schemas.response import APIResponse
from service.dependencies import auth_middleware

router = APIRouter(prefix="/documents", tags=["document"])

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    user: dict = Depends(auth_middleware),
):
    return await document_controller.upload_document(
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