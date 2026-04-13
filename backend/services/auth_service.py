from datetime import datetime, timedelta
from typing import Optional
from passlib.context import CryptContext
from fastapi import HTTPException
from bson import ObjectId

from database import users_collection
from utils.helpers import generate_otp
from utils.jwt_utils import create_access_token
from config.settings import settings

import asyncio

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


class AuthService:

    async def register(self, name: str, email: str, password: str, mobile: Optional[str] = None):

        if users_collection.find_one({"email": email}):
            raise HTTPException(status_code=400, detail="Email already registered")

        otp = generate_otp()
        print(f"📝 Registering user: {email}")
        print(f"🔐 Generated OTP: {otp}")
        expires = datetime.utcnow() + timedelta(minutes=settings.OTP_EXPIRY_MINUTES)

        user_data = {
            "name": name,
            "email": email,
            "mobile": mobile,
            "password": hash_password(password),
            "role": "USER",
            "is_verified": False,
            "otp_code": otp,
            "otp_expires_at": expires
        }

        result = users_collection.insert_one(user_data)
        
        return {
            "message": "Registration successful. Enter the OTP to verify your email.",
            "user_id": str(result.inserted_id),
            "email": email,
            "otp": otp
        }


    def verify_otp(self, email: str, otp: str):

        user = users_collection.find_one({"email": email})

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if user.get("is_verified"):
            raise HTTPException(status_code=400, detail="Already verified")

        if user.get("otp_code") != otp:
            raise HTTPException(status_code=400, detail="Invalid OTP")

        if user.get("otp_expires_at") and datetime.utcnow() > user["otp_expires_at"]:
            raise HTTPException(status_code=400, detail="OTP expired")

        users_collection.update_one(
            {"_id": user["_id"]},
            {"$set": {"is_verified": True, "otp_code": None, "otp_expires_at": None}}
        )

        token = create_access_token({
            "sub": str(user["_id"]),
            "email": user["email"],
            "role": user["role"],
            "name": user["name"]
        })

        return {
            "access_token": token,
            "token_type": "bearer",
            "user": _serialize(user)
        }


    def login(self, email: str, password: str):

        user = users_collection.find_one({"email": email})

        if not user or not verify_password(password, user["password"]):
            raise HTTPException(status_code=401, detail="Invalid email or password")

        if not user.get("is_verified"):
            raise HTTPException(status_code=403, detail="Please verify your email first")

        token = create_access_token({
            "sub": str(user["_id"]),
            "email": user["email"],
            "role": user["role"],
            "name": user["name"]
        })

        return {
            "access_token": token,
            "token_type": "bearer",
            "user": _serialize(user)
        }


    async def forgot_password(self, email: str):

        user = users_collection.find_one({"email": email})

        if not user:
            # Don't reveal if email exists for security, but return false indicator
            return {
                "message": "If that email exists, an OTP has been sent",
                "email": email,
                "otp": None,
                "user_found": False
            }

        otp = generate_otp()

        users_collection.update_one(
            {"_id": user["_id"]},
            {"$set": {
                "otp_code": otp,
                "otp_expires_at": datetime.utcnow() + timedelta(minutes=settings.OTP_EXPIRY_MINUTES)
            }}
        )

        return {
            "message": "OTP generated. Check your email.",
            "email": email,
            "otp": otp,
            "user_found": True
        }


    def reset_password(self, email: str, otp: str, new_password: str):

        user = users_collection.find_one({"email": email})

        if not user or user.get("otp_code") != otp:
            raise HTTPException(status_code=400, detail="Invalid OTP")

        if user.get("otp_expires_at") and datetime.utcnow() > user["otp_expires_at"]:
            raise HTTPException(status_code=400, detail="OTP expired")

        users_collection.update_one(
            {"_id": user["_id"]},
            {"$set": {
                "password": hash_password(new_password),
                "otp_code": None,
                "otp_expires_at": None
            }}
        )

        return {"message": "Password reset successful"}


    async def resend_otp(self, email: str):

        user = users_collection.find_one({"email": email})

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        otp = generate_otp()

        users_collection.update_one(
            {"_id": user["_id"]},
            {"$set": {
                "otp_code": otp,
                "otp_expires_at": datetime.utcnow() + timedelta(minutes=settings.OTP_EXPIRY_MINUTES)
            }}
        )

        return {
            "message": "New OTP generated",
            "email": email,
            "otp": otp
        }


def _serialize(user):
    return {
        "id": str(user["_id"]),
        "name": user["name"],
        "email": user["email"],
        "mobile": user.get("mobile"),
        "role": user["role"],
        "is_verified": user["is_verified"],
    }


def delete_unverified_user(user_id: str) -> bool:
    """Delete unverified user (for rollback after OTP timeout)"""
    try:
        from bson import ObjectId
        result = users_collection.delete_one({"_id": ObjectId(user_id), "is_verified": False})
        if result.deleted_count > 0:
            print(f"🗑️  Deleted unverified user: {user_id}")
            return True
        return False
    except Exception as e:
        print(f"❌ Error deleting user {user_id}: {str(e)}")
        return False


auth_service = AuthService()