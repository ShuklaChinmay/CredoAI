"""
documents.py  –  Document upload & management for loan applications
PUT THIS FILE IN:  backend/routes/documents.py
"""

import os
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from bson import ObjectId

from database import db
from utils.jwt_utils import get_current_user

router = APIRouter(prefix="/documents", tags=["Documents"])

documents_collection = db["documents"]
loans_collection     = db["loans"]
payments_collection  = db["payments"]

UPLOAD_DIR        = "uploads/documents"
ALLOWED_EXT       = {".pdf", ".jpg", ".jpeg", ".png", ".webp"}
MAX_FILE_SIZE     = 10 * 1024 * 1024   # 10 MB

os.makedirs(UPLOAD_DIR, exist_ok=True)

LOAN_DOCUMENTS: dict[str, list[str]] = {
    "home": [
        "Aadhaar Card",
        "PAN Card",
        "Income Proof (Salary Slip / ITR)",
        "Bank Statement (6 Months)",
        "Property Documents",
        "Passport-size Photo",
    ],
    "personal": [
        "Aadhaar Card",
        "PAN Card",
        "Income Proof (Salary Slip / ITR)",
        "Bank Statement (3 Months)",
        "Passport-size Photo",
    ],
    "business": [
        "Aadhaar Card",
        "PAN Card",
        "Business Registration Certificate",
        "Income Tax Returns (2 Years)",
        "Bank Statement (6 Months)",
        "GST Certificate",
    ],
    "car": [
        "Aadhaar Card",
        "PAN Card",
        "Income Proof (Salary Slip)",
        "Bank Statement (3 Months)",
        "Vehicle Quotation / Pro-forma",
        "Passport-size Photo",
    ],
    "education": [
        "Aadhaar Card",
        "PAN Card",
        "College / University Admission Letter",
        "Fee Structure Document",
        "Parent / Guardian Income Proof",
        "Marksheets (Last 2 Years)",
    ],
    "default": [
        "Aadhaar Card",
        "PAN Card",
        "Income Proof",
        "Bank Statement (3 Months)",
        "Passport-size Photo",
    ],
}


def _get_loan(loan_id: str, user_id: str):
    try:
        loan = loans_collection.find_one(
            {"_id": ObjectId(loan_id), "user_id": user_id}
        )
    except Exception:
        raise HTTPException(status_code=404, detail="Loan not found")
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found or unauthorised")
    return loan


@router.get("/required/{loan_id}")
def get_required_documents(
    loan_id: str,
    current_user: dict = Depends(get_current_user),
):
    loan      = _get_loan(loan_id, current_user["id"])
    loan_type = loan.get("loan_type", "default").lower()
    required  = LOAN_DOCUMENTS.get(loan_type, LOAN_DOCUMENTS["default"])

    uploaded      = list(documents_collection.find({"loan_id": loan_id, "user_id": current_user["id"]}))
    uploaded_map  = {d["document_name"]: d for d in uploaded}

    docs_status = [
        {
            "name":      name,
            "uploaded":  name in uploaded_map,
            "file_url":  uploaded_map[name].get("file_url") if name in uploaded_map else None,
            "file_name": uploaded_map[name].get("file_name") if name in uploaded_map else None,
        }
        for name in required
    ]

    all_uploaded  = all(d["uploaded"] for d in docs_status)
    payment_done  = False
    if all_uploaded:
        pay = payments_collection.find_one(
            {"loan_application_id": loan_id, "payment_completed": True}
        )
        payment_done = bool(pay)

    return {
        "loan_id":        loan_id,
        "loan_type":      loan_type,
        "loan_amount":    loan.get("requested_amount"),
        "loan_purpose":   loan.get("purpose"),
        "loan_status":    loan.get("status"),
        "documents":      docs_status,
        "all_uploaded":   all_uploaded,
        "payment_done":   payment_done,
    }


@router.post("/upload/{loan_id}")
async def upload_document(
    loan_id: str,
    document_name: str = Form(...),
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    _get_loan(loan_id, current_user["id"])

    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(
            status_code=400,
            detail=f"File type '{ext}' not allowed. Use: {', '.join(ALLOWED_EXT)}",
        )

    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Max 10 MB allowed.")

    safe_name = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(UPLOAD_DIR, safe_name)
    with open(file_path, "wb") as f:
        f.write(contents)

    file_url = f"/uploads/documents/{safe_name}"

    documents_collection.update_one(
        {
            "loan_id":       loan_id,
            "user_id":       current_user["id"],
            "document_name": document_name,
        },
        {
            "$set": {
                "loan_id":       loan_id,
                "user_id":       current_user["id"],
                "document_name": document_name,
                "file_name":     file.filename,
                "file_url":      file_url,
                "file_size":     len(contents),
                "uploaded_at":   datetime.utcnow(),
            }
        },
        upsert=True,
    )

    return {
        "success":       True,
        "document_name": document_name,
        "file_url":      file_url,
        "message":       f"'{document_name}' uploaded successfully",
    }


@router.delete("/{loan_id}/{document_name:path}")
def delete_document(
    loan_id: str,
    document_name: str,
    current_user: dict = Depends(get_current_user),
):
    doc = documents_collection.find_one(
        {
            "loan_id":       loan_id,
            "user_id":       current_user["id"],
            "document_name": document_name,
        }
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    try:
        disk_path = doc["file_url"].lstrip("/")
        if os.path.exists(disk_path):
            os.remove(disk_path)
    except Exception:
        pass

    documents_collection.delete_one({"_id": doc["_id"]})
    return {"success": True, "message": "Document removed"}


@router.post("/submit/{loan_id}")
def submit_application(
    loan_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Called after payment is verified.
    Marks the loan status as 'documents_submitted'.
    """
    loan = _get_loan(loan_id, current_user["id"])

    payment = payments_collection.find_one(
        {"loan_application_id": loan_id, "payment_completed": True}
    )
    if not payment:
        raise HTTPException(
            status_code=402,
            detail="Payment not completed. Please complete payment before submitting.",
        )

    loan_type = loan.get("loan_type", "default").lower()
    required  = LOAN_DOCUMENTS.get(loan_type, LOAN_DOCUMENTS["default"])
    uploaded  = documents_collection.count_documents(
        {"loan_id": loan_id, "user_id": current_user["id"]}
    )
    if uploaded < len(required):
        raise HTTPException(
            status_code=400,
            detail=f"Upload all {len(required)} required documents first.",
        )

    loans_collection.update_one(
        {"_id": ObjectId(loan_id)},
        {
            "$set": {
                "status":       "documents_submitted",
                "submitted_at": datetime.utcnow(),
            }
        },
    )

    return {
        "success": True,
        "message": "Application submitted successfully with all documents",
    }
