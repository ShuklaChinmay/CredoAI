from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from bson import ObjectId
from database import db
from utils.jwt_utils import require_admin

router = APIRouter(prefix="/admin", tags=["Admin"])

loan_collection = db["loans"]
user_collection = db["users"]
product_collection = db["loan_products"]
documents_collection = db["documents"]
payments_collection = db["payments"]


class UpdateStatusRequest(BaseModel):
    status: str
    reason: Optional[str] = None


class LoanProductCreate(BaseModel):
    name: str
    loan_type: str
    icon: Optional[str] = "💰"
    product_code: Optional[str] = None
    loan_provider_bank: Optional[str] = ""
    min_amount: float = 50000
    max_amount: float = 2500000
    interest_rate: float = 10.5
    min_tenure_months: int = 12
    max_tenure_months: int = 60
    residual_income: float = 25000
    min_credit_score: int = 650
    max_credit_score: int = 900
    processing_fee_pct: float = 1.0
    description: Optional[str] = ""
    features: Optional[List[str]] = []
    documents_needed: Optional[List[str]] = []
    loan_conditions: Optional[List[str]] = []
    is_active: bool = True
    sort_order: int = 0


class LoanProductUpdate(BaseModel):
    name: Optional[str] = None
    loan_type: Optional[str] = None
    icon: Optional[str] = None
    loan_provider_bank: Optional[str] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    interest_rate: Optional[float] = None
    min_tenure_months: Optional[int] = None
    max_tenure_months: Optional[int] = None
    residual_income: Optional[float] = None
    min_credit_score: Optional[int] = None
    max_credit_score: Optional[int] = None
    processing_fee_pct: Optional[float] = None
    description: Optional[str] = None
    features: Optional[List[str]] = None
    documents_needed: Optional[List[str]] = None
    loan_conditions: Optional[List[str]] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None


@router.get("/applications")
def get_all_applications(current_user: dict = Depends(require_admin)):
    """Get all loan applications with detailed user and document information"""
    apps = list(loan_collection.find({}))
    
    detailed_apps = []
    for app in apps:
        user_id = app.get("user_id")
        user = None
        if user_id:
            try:
                # Try with ObjectId first
                if isinstance(user_id, ObjectId):
                    user = user_collection.find_one({"_id": user_id})
                else:
                    try:
                        user = user_collection.find_one({"_id": ObjectId(str(user_id))})
                    except:
                        user = user_collection.find_one({"_id": user_id})
            except:
                pass
        
        docs = list(documents_collection.find(
            {"loan_id": str(app.get("_id"))}
        ))
        
        payment = payments_collection.find_one(
            {"loan_application_id": str(app.get("_id"))}
        )
        
        documents_list = [
            {
                "type": doc.get("document_name"),
                "file_path": doc.get("file_url"),
                "uploaded_at": str(doc.get("uploaded_at")) if doc.get("uploaded_at") else None,
                "size": doc.get("file_size"),
            }
            for doc in docs
        ]
        
        detailed_apps.append({
            "id": str(app.get("_id")),
            "user_id": str(app.get("user_id", "")),
            "user_name": user.get("name") if user else "Unknown User",
            "user_email": user.get("email") if user else "N/A",
            "loan_type": app.get("loan_type"),
            "requested_amount": float(app.get("requested_amount", 0)),
            "payment_completed": bool(app.get("payment_completed", False)),
            "payment_id": str(payment.get("_id")) if payment else None,
            "status": app.get("status"),
            "created_at": str(app.get("created_at")) if app.get("created_at") else None,
            "updated_at": str(app.get("updated_at")) if app.get("updated_at") else None,
            "documents": documents_list,
            "document_count": len(documents_list),
            "reason": app.get("reason"),
        })
    
    return {"applications": detailed_apps}


@router.get("/applications/{loan_id}/details")
def get_application_details(
    loan_id: str,
    current_user: dict = Depends(require_admin)
):
    """Get detailed information about a specific loan application"""
    try:
        app = loan_collection.find_one({"_id": ObjectId(loan_id)})
    except:
        app = loan_collection.find_one({"_id": loan_id})
    
    if not app:
        raise HTTPException(status_code=404, detail="Loan application not found")
    
    user_id = app.get("user_id")
    user = None
    if user_id:
        try:
            if isinstance(user_id, ObjectId):
                user = user_collection.find_one({"_id": user_id})
            else:
                try:
                    user = user_collection.find_one({"_id": ObjectId(str(user_id))})
                except:
                    user = user_collection.find_one({"_id": user_id})
        except:
            pass
    
    docs = list(documents_collection.find(
        {"loan_id": str(app.get("_id"))}
    ))
    
    payment = payments_collection.find_one(
        {"loan_application_id": str(app.get("_id"))}
    )
    
    return {
        "id": str(app.get("_id")),
        "user": {
            "id": str(user.get("_id")) if user else None,
            "name": user.get("name") if user else "Unknown User",
            "email": user.get("email") if user else "N/A",
            "phone": user.get("phone") if user else "N/A",
            "created_at": str(user.get("created_at")) if user and user.get("created_at") else None,
        },
        "loan": {
            "type": app.get("loan_type"),
            "requested_amount": float(app.get("requested_amount", 0)),
            "status": app.get("status"),
            "created_at": str(app.get("created_at")) if app.get("created_at") else None,
            "updated_at": str(app.get("updated_at")) if app.get("updated_at") else None,
            "reason": app.get("reason"),
        },
        "payment": {
            "completed": bool(app.get("payment_completed", False)),
            "payment_id": str(payment.get("_id")) if payment else None,
            "razorpay_order_id": payment.get("razorpay_order_id") if payment else None,
            "amount": int(payment.get("amount", 0)) if payment else None,
        },
        "documents": [
            {
                "type": doc.get("document_name"),
                "file_path": doc.get("file_url"),
                "uploaded_at": str(doc.get("uploaded_at")) if doc.get("uploaded_at") else None,
                "size": doc.get("file_size"),
            }
            for doc in docs
        ],
    }


@router.put("/applications/{loan_id}")
def update_application(
    loan_id: str,
    body: UpdateStatusRequest,
    current_user: dict = Depends(require_admin),
):
    """Update loan application status with optional reason"""
    try:
        obj_id = ObjectId(loan_id)
    except:
        obj_id = loan_id
    
    update_data = {
        "status": body.status,
        "updated_at": datetime.utcnow(),
    }
    
    if body.reason:
        update_data["reason"] = body.reason
    
    result = loan_collection.update_one(
        {"_id": obj_id},
        {"$set": update_data}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Loan not found")

    return {"message": f"Application {body.status}", "updated": True}


@router.delete("/applications/{loan_id}")
def delete_application(
    loan_id: str,
    current_user: dict = Depends(require_admin),
):
    """Delete a rejected loan application"""
    try:
        obj_id = ObjectId(loan_id)
    except:
        obj_id = loan_id
    
    app = loan_collection.find_one({"_id": obj_id})
    
    if not app:
        raise HTTPException(status_code=404, detail="Loan not found")
    
    if app.get("status") != "rejected":
        raise HTTPException(status_code=400, detail="Only rejected applications can be deleted")
    
    # Delete the application
    loan_collection.delete_one({"_id": obj_id})
    
    return {"message": "Application deleted successfully", "deleted": True}


@router.get("/users")
def get_all_users(current_user: dict = Depends(require_admin)):
    users = list(user_collection.find({}, {"password": 0}))

    for u in users:
        u["id"] = str(u["_id"])
        del u["_id"]

    return {"users": users}


@router.delete("/users/{user_id}")
def delete_user(
    user_id: str,
    current_user: dict = Depends(require_admin),
):
    result = user_collection.delete_one({"_id": ObjectId(user_id)})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")

    return {"message": "User deleted successfully"}

@router.get("/stats")
def get_stats(current_user: dict = Depends(require_admin)):
    total = loan_collection.count_documents({})
    approved = loan_collection.count_documents({"status": "approved"})
    rejected = loan_collection.count_documents({"status": "rejected"})
    submitted = loan_collection.count_documents({"status": "kyc_pending"})
    total_users = user_collection.count_documents({})
    total_schemes = product_collection.count_documents({})

    return {
        "total_applications": total,
        "approved": approved,
        "rejected": rejected,
        "submitted": submitted,
        "total_users": total_users,
        "total_schemes": total_schemes,
    }

@router.get("/schemes")
def list_all_schemes(current_user: dict = Depends(require_admin)):
    schemes = list(product_collection.find({}))
    for s in schemes:
        s["id"] = str(s["_id"])
        s["_id"] = str(s["_id"])
    return {"schemes": schemes}


@router.get("/schemes/{scheme_id}")
def get_scheme(scheme_id: str, current_user: dict = Depends(require_admin)):
    try:
        obj_id = ObjectId(scheme_id)
    except:
        obj_id = scheme_id
    
    scheme = product_collection.find_one({"_id": obj_id})

    if not scheme:
        raise HTTPException(status_code=404, detail="Scheme not found")

    scheme["id"] = str(scheme["_id"])
    scheme["_id"] = str(scheme["_id"])
    return scheme


@router.post("/schemes", status_code=201)
def create_scheme(body: LoanProductCreate, current_user: dict = Depends(require_admin)):
    result = product_collection.insert_one(body.dict())
    scheme = product_collection.find_one({"_id": result.inserted_id})
    scheme["id"] = str(scheme["_id"])
    scheme["_id"] = str(scheme["_id"])
    return {"scheme": scheme}


@router.put("/schemes/{scheme_id}")
def update_scheme(
    scheme_id: str,
    body: LoanProductUpdate,
    current_user: dict = Depends(require_admin),
):
    try:
        obj_id = ObjectId(scheme_id)
    except:
        obj_id = scheme_id
    
    data = {k: v for k, v in body.dict().items() if v is not None}

    result = product_collection.update_one(
        {"_id": obj_id},
        {"$set": data}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Scheme not found")

    scheme = product_collection.find_one({"_id": obj_id})
    scheme["id"] = str(scheme["_id"])
    scheme["_id"] = str(scheme["_id"])
    return {"scheme": scheme}


@router.patch("/schemes/{scheme_id}/toggle")
def toggle_scheme(scheme_id: str, current_user: dict = Depends(require_admin)):
    try:
        obj_id = ObjectId(scheme_id)
    except:
        obj_id = scheme_id
    
    scheme = product_collection.find_one({"_id": obj_id})

    if not scheme:
        raise HTTPException(status_code=404, detail="Scheme not found")

    new_status = not scheme.get("is_active", True)

    product_collection.update_one(
        {"_id": obj_id},
        {"$set": {"is_active": new_status}}
    )

    updated_scheme = product_collection.find_one({"_id": obj_id})
    updated_scheme["id"] = str(updated_scheme["_id"])
    updated_scheme["_id"] = str(updated_scheme["_id"])
    return {"scheme": updated_scheme}


@router.delete("/schemes/{scheme_id}")
def delete_scheme(scheme_id: str, current_user: dict = Depends(require_admin)):
    try:
        obj_id = ObjectId(scheme_id)
    except:
        obj_id = scheme_id
    
    scheme = product_collection.find_one({"_id": obj_id})
    
    if not scheme:
        raise HTTPException(status_code=404, detail="Scheme not found")
    
    result = product_collection.delete_one({"_id": obj_id})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Scheme not found")

    return {"message": "Scheme deleted"}