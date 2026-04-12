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
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


async def send_otp_email(email: str, otp: str) -> bool:
    """Send OTP via SMTP (Gmail)"""
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Your CredoAI OTP Verification Code"
        msg["From"] = settings.SMTP_USER
        msg["To"] = email

        # Create HTML and plain text versions
        text = f"Your OTP code is: {otp}\n\nThis code will expire in {settings.OTP_EXPIRY_MINUTES} minutes."
        html = f"""
        <html>
            <head></head>
            <body>
                <h2>Your CredoAI OTP</h2>
                <p>Your verification code is: <strong>{otp}</strong></p>
                <p>This code will expire in {settings.OTP_EXPIRY_MINUTES} minutes.</p>
                <p>If you didn't request this, please ignore this email.</p>
            </body>
        </html>
        """
        
        msg.attach(MIMEText(text, "plain"))
        msg.attach(MIMEText(html, "html"))

        # Port 587 = SMTP with STARTTLS
        async with aiosmtplib.SMTP(hostname=settings.SMTP_HOST, port=settings.SMTP_PORT, timeout=10) as smtp:
            print(f"🔌 Connecting to {settings.SMTP_HOST}:{settings.SMTP_PORT}")
            await smtp.starttls()
            print(f"🔒 TLS secured")
            await smtp.login(settings.SMTP_USER, settings.SMTP_PASS)
            print(f"✅ Authenticated as {settings.SMTP_USER}")
            await smtp.send_message(msg)
        
        print(f"✅ OTP email sent successfully to {email}")
        return True
        
    except Exception as e:
        print(f"❌ SMTP Error sending OTP to {email}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


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
        
        # Send OTP email asynchronously (don't wait for it)
        # This prevents timeout on the registration endpoint
        asyncio.create_task(send_otp_email(email, otp))

        return {
            "message": "Registration successful. OTP has been sent to your email.",
            "user_id": str(result.inserted_id)
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
            return {"message": "If that email exists, an OTP has been sent"}

        otp = generate_otp()

        users_collection.update_one(
            {"_id": user["_id"]},
            {"$set": {
                "otp_code": otp,
                "otp_expires_at": datetime.utcnow() + timedelta(minutes=settings.OTP_EXPIRY_MINUTES)
            }}
        )

        # Send email asynchronously (don't wait)
        asyncio.create_task(send_otp_email(email, otp))

        return {"message": "OTP sent to your email"}


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

        # Send email asynchronously (don't wait)
        asyncio.create_task(send_otp_email(email, otp))

        return {"message": "OTP resent to your email"}


def _serialize(user):
    return {
        "id": str(user["_id"]),
        "name": user["name"],
        "email": user["email"],
        "mobile": user.get("mobile"),
        "role": user["role"],
        "is_verified": user["is_verified"],
    }


auth_service = AuthService()