from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from database import db
from utils.helpers import calculate_emi
from utils.jwt_utils import get_current_user

router = APIRouter(prefix="/loan", tags=["Loan"])

loan_collection = db["loans"]
product_collection = db["loan_products"]


class EMIRequest(BaseModel):
    principal: float
    annual_rate: float
    tenure_months: int


class ApplyRequest(BaseModel):
    loan_type: str
    requested_amount: float
    purpose: Optional[str] = None


@router.get("/products")
def get_active_products():
    products = list(product_collection.find({"is_active": True}, {"_id": 0}))
    return {"products": products}


@router.post("/emi")
def calculate_emi_endpoint(body: EMIRequest):
    emi = calculate_emi(body.principal, body.annual_rate, body.tenure_months)
    total = round(emi * body.tenure_months, 2)
    interest = round(total - body.principal, 2)

    return {
        "monthly_emi": emi,
        "total_payable": total,
        "total_interest": interest,
        "principal": body.principal,
        "tenure_months": body.tenure_months,
        "annual_rate": body.annual_rate,
    }


@router.get("/credit-score")
def get_credit_score(
    monthly_income: float,
    loan_amount: float,
    existing_emi: float = 0,
    current_user: dict = Depends(get_current_user),
):
    ratio = loan_amount / (monthly_income * 12) if monthly_income > 0 else 99
    foir = existing_emi / monthly_income if monthly_income > 0 else 1

    base = 750
    if ratio > 5:
        base -= 100
    elif ratio > 3:
        base -= 50

    if foir > 0.5:
        base -= 80
    elif foir > 0.3:
        base -= 40

    if monthly_income >= 100000:
        base += 30
    elif monthly_income >= 50000:
        base += 15

    score = max(300, min(900, base))

    if score >= 750:
        band, advice = "Excellent", "You qualify for the best rates!"
    elif score >= 700:
        band, advice = "Good", "Competitive rates available."
    elif score >= 650:
        band, advice = "Fair", "Standard rates available."
    elif score >= 600:
        band, advice = "Below Average", "Reduce existing debt first."
    else:
        band, advice = "Poor", "Only secured loans available."

    return {"credit_score": score, "band": band, "advice": advice}


@router.post("/apply")
def apply_loan(
    body: ApplyRequest,
    current_user: dict = Depends(get_current_user),
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    loan_data = {
        "user_id": current_user["id"],
        "loan_type": body.loan_type,
        "requested_amount": body.requested_amount,
        "purpose": body.purpose,
        "status": "initiated",
        "created_at": datetime.utcnow(),
    }

    result = loan_collection.insert_one(loan_data)

    return {
        "message": "Application created",
        "loan_id": str(result.inserted_id),
    }


@router.get("/user")
def get_user_applications(
    current_user: dict = Depends(get_current_user),
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    raw_loans = list(loan_collection.find({"user_id": current_user["id"]}))
    loans = []
    for loan in raw_loans:
        loan["loan_id"] = str(loan.pop("_id"))
        loans.append(loan)


    return {"applications": loans}


@router.get("/status/{loan_id}")
def get_loan_status(
    loan_id: str,
    current_user: dict = Depends(get_current_user),
):
    loan = loan_collection.find_one({"_id": loan_id})

    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")

    loan["_id"] = str(loan["_id"])
    return loan