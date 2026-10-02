from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from core.config import settings
# from schemas.users import User # Assuming you have a User schema

# Define the scheme so FastAPI knows to look for a Bearer token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

async def auth_middleware(token :str = Depends(oauth2_scheme)):
    
    if not token:
        raise HTTPException(
            status_code=500,
            detail ="Invalid Token"
        )
        

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail ="Could not validate the credentails",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    
    try:
        payload = jwt.decode(token , settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        
        print("payload ======= 21", payload)
        
        user_id:str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception 
    
    return {"id": user_id}