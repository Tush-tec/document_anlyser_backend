# schema/users.py
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional


# ============ REQUEST SCHEMAS (what client sends) ============

class UserRegister(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=100)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class GoogleUserData(BaseModel):
    google_id: str
    email: EmailStr
    name: str
    picture: Optional[str] = None


# ============ DB DOCUMENT BUILDERS (server-side only) ============

def user_documents(name: str, username: str, email: str, hashed_password: str) -> dict:
    now = datetime.utcnow()
    return {
        "name": name,
        "username": username,
        "email": email.lower().strip(),
        "password": hashed_password,
        "auth_provider": "local",
        "google_id": None,
        "picture": None,
        "created_at": now,
        "updated_at": now,
    }


def google_user_document(data: GoogleUserData) -> dict:
    now = datetime.utcnow()
    return {
        "google_id": data.google_id,
        "email": data.email.lower().strip(),
        "name": data.name,
        "username": f"{data.name[:4].lower()}_{data.google_id[-4:]}",
        "picture": data.picture,
        "password": None,
        "auth_provider": "google",
        "created_at": now,
        "updated_at": now,
    }