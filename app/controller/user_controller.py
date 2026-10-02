from datetime import datetime
from bson import ObjectId
from fastapi import HTTPException, status
import random
from core.db import users_collection
from schemas.users import UserRegister, UserLogin, user_documents
from utils.security import create_access_token, hash_password, decode_token, verify_password
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from core.config import settings
from schemas.users import GoogleUserData, google_user_document


async def register_user(register: UserRegister) -> dict:
    """
    Register user by checking that no duplicate user in db
    """
    
    
    email = register.email.lower().strip()
    
    existing = users_collection.find_one({"email" : email})
    
    if existing: 
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    name = register.name.strip()

    doc = user_documents(
        name=name,
        username=f"{name[:4]}_{random.randint(100, 999)}",
        email=email,
        hashed_password=hash_password(register.password),
    )

    result = users_collection.insert_one(doc)
    token = create_access_token(str(result.inserted_id))
    
    return {
        "status_code"  : 200,
        "message" : "User Created Successfully",
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": str(result.inserted_id),
            "name": doc["name"],
            "email": doc["email"],
        },
    }
    
    
async def login (request : UserLogin) -> dict:
    email = request.email.lower().strip()
    
    
    # Find user exist in our application
    user = users_collection.find_one({"email" : email})
    
    if not user or not verify_password(request.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
        
        
    token = create_access_token(str(user["_id"]))
    
    return {
        "status_code"  : 200,
        "message" : "User login Successfully",
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": str(user["_id"]),
            "name": user["name"],
            "email": user["email"],
        },
    }
    
async def get_current_user(user_id: str) -> dict:
    user = users_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return {
        "id": str(user["_id"]),
        "name": user["name"],
        "email": user["email"],
    }


# Google login

async def google_login(token: str) -> dict:
    """Verify Google ID token and return app JWT."""

    # 1. Verify the Google token
    try:
        idinfo = id_token.verify_oauth2_token(
            token,
            google_requests.Request(),
            settings.GOOGLE_CLIENT_ID,
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google token",
        )

    # 2. Check issuer
    if idinfo["iss"] not in ["accounts.google.com", "https://accounts.google.com"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Wrong issuer",
        )

    google_id = idinfo["sub"]
    email = idinfo["email"].lower().strip()
    name = idinfo.get("name", email.split("@")[0])
    picture = idinfo.get("picture")

    # 3. Find existing user (by google_id OR email)
    user = users_collection.find_one({
        "$or": [{"google_id": google_id}, {"email": email}]
    })

    if user:
        # Link google_id if user signed up with email/password first
        if not user.get("google_id"):
            users_collection.update_one(
                {"_id": user["_id"]},
                {"$set": {"google_id": google_id, "picture": picture}},
            )
        user_id = str(user["_id"])
        user_name = user["name"]
    else:
        # Create new user
        doc = google_user_document(GoogleUserData(
            google_id=google_id,
            email=email,
            name=name,
            picture=picture,
        ))
        result = users_collection.insert_one(doc)
        user_id = str(result.inserted_id)
        user_name = name

    # 4. Issue your own JWT
    token = create_access_token(user_id)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {"id": user_id, "name": user_name, "email": email},
    }
