from fastapi import APIRouter

from route.auth_routes import router as auth_router
from route.document_routes import router as document_controller

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(document_controller)