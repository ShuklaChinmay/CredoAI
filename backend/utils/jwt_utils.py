from datetime import datetime, timedelta
from typing import Optional
from bson import ObjectId
from jose import JWTError, jwt
from fastapi import HTTPException, status, Depends, Header

from config.settings import settings
from database import users_collection


# ✅ CREATE TOKEN
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


# ✅ DECODE TOKEN
def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ✅ GET CURRENT USER (Mongo Version)
def get_current_user(authorization: Optional[str] = Header(None)) -> dict | None:
    
    # DEBUG MODE → allow without auth
    if settings.DEBUG:
        if not authorization:
            return None

        try:
            scheme, token = authorization.split()
            if scheme.lower() != "bearer":
                return None

            payload = decode_token(token)
            user_id = payload.get("sub")

            if not user_id:
                return None

            user = users_collection.find_one({"_id": ObjectId(user_id)})

            if not user:
                return None

            return {
                "id": str(user["_id"]),
                "role": user["role"],
                "email": user["email"],
                "name": user["name"],
            }

        except Exception:
            return None


    # 🔐 PRODUCTION MODE
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing credentials")

    try:
        scheme, token = authorization.split()

        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid auth scheme")

        payload = decode_token(token)
        user_id = payload.get("sub")

        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")

        user = users_collection.find_one({"_id": user_id})

        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        return {
            "id": str(user["_id"]),
            "role": user["role"],
            "email": user["email"],
            "name": user["name"],
        }

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")


# ✅ ADMIN CHECK
def require_admin(current_user: dict | None = Depends(get_current_user)) -> dict:

    if settings.DEBUG:
        return current_user or {
            "id": "999",
            "role": "ADMIN",
            "email": "debug@debug.com",
        }

    if not current_user or current_user.get("role") != "ADMIN":
        raise HTTPException(status_code=403, detail="Admin access required")

    return current_user