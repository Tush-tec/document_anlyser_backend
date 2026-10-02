# routes/auth_routes.py
from fastapi import APIRouter, Depends
from schemas.users import UserRegister, UserLogin
from controller import user_controller
from utils.auth_dependancy import require_auth
from pydantic import BaseModel


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup")
async def signup(payload: UserRegister):
    return await user_controller.register_user(payload)


@router.post("/login")
async def login(payload: UserLogin):
    return await user_controller.login(payload)


@router.get("/me")
async def me(user: dict = Depends(require_auth)):
    return user

class GoogleTokenPayload(BaseModel):
    token: str


@router.post("/google")
async def google_login(payload: GoogleTokenPayload):
    return await user_controller.google_login(payload.token)
