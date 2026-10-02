from fastapi import Depends, HTTPException, Header
from core.db import get_db
from core.security import decode_token
from models.models import User
from bson import ObjectId

def get_current_user(
    authorization: str = Header(...),
    db = Depends(get_db),
) -> User:
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "missing bearer")
    try:
        uid = decode_token(authorization.removeprefix("Bearer ").strip())
    except ValueError:
        raise HTTPException(401, "invalid token")
    
    # Fetch user from MongoDB
    try:
        user_doc = db.users.find_one({"_id": ObjectId(uid)})
    except Exception:
        raise HTTPException(401, "invalid user id")
    
    if not user_doc:
        raise HTTPException(401, "user not found")
    
    # Convert MongoDB doc to User model
    user = User(**{**user_doc, "id": str(user_doc["_id"])})
    return user