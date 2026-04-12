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
# import aiosmtplib
# from email.mime.text import MIMEText
# from email.mime.multipart import MIMEMultipart
import requests

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# async def send_otp_email(email: str, otp: str) -> bool:
#     try:
#         msg = MIMEMultipart("alternative")
#         msg["Subject"] = "Your CredoAI OTP Verification Code"
#         msg["From"] = settings.SMTP_USER
#         msg["To"] = email

#         text = f"Your OTP code is: {otp}"
#         msg.attach(MIMEText(text, "plain"))

#         await aiosmtplib.send(
#             msg,
#             hostname=settings.SMTP_HOST,
#             port=settings.SMTP_PORT,
#             username=settings.SMTP_USER,
#             password=settings.SMTP_PASS,
#             start_tls=True,
#         )
#         return True
#     except Exception as e:          # for testing purposes, catch all exceptions and print the error. In production, consider logging this instead.
#         print("Email sending error:", e)  
#         return False

def send_otp_email(email: str, otp: str) -> bool:
    try:
        response = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {settings.RESEND_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "from": "onboarding@resend.dev",
                "to": [email],
                "subject": "Your CredoAI OTP",
                "html": f"<h2>Your OTP is: {otp}</h2>",
            },
        )

        print("Resend response:", response.status_code, response.text)

        return response.status_code in [200, 202]

    except Exception as e:
        print("Resend error:", e)
        return False


class AuthService:

    async def register(self, name: str, email: str, password: str, mobile: Optional[str] = None):

        if users_collection.find_one({"email": email}):
            raise HTTPException(status_code=400, detail="Email already registered")

        otp = generate_otp()
        print("OTP:", otp)          # For testing purposes, print the OTP to the console. Remove this in production.
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

        email_sent = send_otp_email(email, otp)           # For testing purposes, we will print the OTP to the console instead of sending an email. In production, this should be removed and the email sending functionality should be used.
        if not email_sent:
            raise HTTPException(status_code=500, detail="Failed to send OTP email")

        return result


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

        send_otp_email(email, otp)

        return {"message": "OTP sent"}


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

        send_otp_email(email, otp)

        return {"message": "OTP resent"}


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