import secrets
import hmac
import hashlib
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from database import db
from utils.jwt_utils import get_current_user
from config.settings import settings

router = APIRouter(prefix="/payment", tags=["Payment"])

payment_collection = db["payments"]

UPI_AMOUNT   = 199
UPI_AMOUNT_P = 19900


class CreateOrderRequest(BaseModel):
    loan_application_id: str


class VerifyPaymentRequest(BaseModel):
    loan_application_id: str
    utr: str
    payment_method: str = "upi"


class RazorpayVerifyRequest(BaseModel):
    loan_application_id: str
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


def _generate_order_id(loan_application_id: str) -> str:
    return f"LOANAI-{loan_application_id[-6:]}-{secrets.token_hex(4).upper()}"


@router.post("/create-order")
def create_upi_order(
    body: CreateOrderRequest,
    current_user: dict = Depends(get_current_user),
):
    user_id  = current_user["id"]
    order_id = _generate_order_id(body.loan_application_id)

    payment_collection.update_one(
        {"loan_application_id": body.loan_application_id},
        {
            "$set": {
                "loan_application_id": body.loan_application_id,
                "user_id":             user_id,
                "order_id":            order_id,
                "payment_completed":   False,
                "created_at":          datetime.utcnow(),
            }
        },
        upsert=True,
    )

    vpa     = settings.UPI_VPA
    payee   = settings.UPI_PAYEE_NAME
    note    = f"Doc fee {order_id}"
    upi_url = (
        f"upi://pay?pa={vpa}&pn={payee}"
        f"&am={UPI_AMOUNT}.00&cu=INR&tn={note}&tr={order_id}"
    )

    return {
        "order_id":     order_id,
        "amount":       UPI_AMOUNT,
        "currency":     "INR",
        "upi_id":       vpa,
        "payee_name":   payee,
        "upi_deeplink": upi_url,
        "qr_data":      upi_url,
        "note":         note,
    }


@router.post("/create-razorpay-order")
def create_razorpay_order(
    body: CreateOrderRequest,
    current_user: dict = Depends(get_current_user),
):
    print(f"[DEBUG] create_razorpay_order called with loan_id: {body.loan_application_id}")
    print(f"[DEBUG] current_user: {current_user}")
    print(f"[DEBUG] RAZORPAY_KEY_ID: {settings.RAZORPAY_KEY_ID[:10] if settings.RAZORPAY_KEY_ID else 'NOT SET'}...")
    print(f"[DEBUG] RAZORPAY_KEY_SECRET: {settings.RAZORPAY_KEY_SECRET[:10] if settings.RAZORPAY_KEY_SECRET else 'NOT SET'}...")
    
    if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
        raise HTTPException(
            status_code=501,
            detail="Razorpay is not configured. Add RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET to .env",
        )

    try:
        import razorpay
        print("[DEBUG] razorpay module imported successfully")
    except ImportError as e:
        print(f"[ERROR] Failed to import razorpay: {e}")
        raise HTTPException(status_code=500, detail="razorpay package not installed. Run: pip install razorpay")

    try:
        print("[DEBUG] Creating Razorpay client...")
        rzp_client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )
        
        receipt   = _generate_order_id(body.loan_application_id)
        print(f"[DEBUG] Generated receipt: {receipt}")
        
        print("[DEBUG] Creating Razorpay order...")
        rzp_order = rzp_client.order.create(
            {
                "amount":          UPI_AMOUNT_P,
                "currency":        "INR",
                "receipt":         receipt,
                "payment_capture": 1,
                "notes": {
                    "loan_application_id": body.loan_application_id,
                    "user_id":             current_user["id"],
                },
            }
        )
        print(f"[DEBUG] Razorpay order created: {rzp_order['id']}")

        print("[DEBUG] Updating payment collection...")
        payment_collection.update_one(
            {"loan_application_id": body.loan_application_id},
            {
                "$set": {
                    "loan_application_id": body.loan_application_id,
                    "user_id":             current_user["id"],
                    "razorpay_order_id":   rzp_order["id"],
                    "order_id":            receipt,
                    "payment_completed":   False,
                    "created_at":          datetime.utcnow(),
                }
            },
            upsert=True,
        )
        print("[DEBUG] Payment collection updated")

        response = {
            "order_id":  rzp_order["id"],
            "amount":    UPI_AMOUNT_P,
            "currency":  "INR",
            "key_id":    settings.RAZORPAY_KEY_ID,
            "receipt":   receipt,
        }
        print(f"[DEBUG] Returning response: {response}")
        return response
    
    except Exception as e:
        import traceback
        error_details = str(e)
        traceback_str = traceback.format_exc()
        print(f"[ERROR] Razorpay Error: {error_details}")
        print(f"[ERROR] Traceback: {traceback_str}")
        raise HTTPException(
            status_code=500,
            detail=f"Razorpay error: {error_details}. Check server logs for details."
        )

@router.get("/config-test")
def test_razorpay_config():
    """Debug endpoint to test if Razorpay is configured correctly"""
    razorpay_available = False
    try:
        import razorpay
        razorpay_available = True
    except ImportError:
        pass
    
    return {
        "razorpay_installed": razorpay_available,
        "razorpay_key_id_set": bool(settings.RAZORPAY_KEY_ID),
        "razorpay_key_secret_set": bool(settings.RAZORPAY_KEY_SECRET),
        "razorpay_key_id": settings.RAZORPAY_KEY_ID[:10] + "..." if settings.RAZORPAY_KEY_ID else "NOT SET",
        "razorpay_key_secret": settings.RAZORPAY_KEY_SECRET[:10] + "..." if settings.RAZORPAY_KEY_SECRET else "NOT SET",
    }

    return {
        "order_id":  rzp_order["id"],
        "amount":    UPI_AMOUNT_P,
        "currency":  "INR",
        "key_id":    settings.RAZORPAY_KEY_ID,
        "receipt":   receipt,
    }


@router.post("/verify")
def verify_upi_payment(
    body: VerifyPaymentRequest,
    current_user: dict = Depends(get_current_user),
):
    if not body.utr or len(body.utr.strip()) < 6:
        raise HTTPException(status_code=400, detail="Invalid UTR number")

    payment = payment_collection.find_one({"loan_application_id": body.loan_application_id})
    if not payment:
        raise HTTPException(status_code=404, detail="Payment record not found")

    payment_collection.update_one(
        {"_id": payment["_id"]},
        {
            "$set": {
                "payment_completed": True,
                "payment_id":        body.utr.strip(),
                "payment_amount":    float(UPI_AMOUNT),
                "payment_method":    body.payment_method,
                "status":            "submitted",
                "submitted_at":      datetime.utcnow(),
            }
        },
    )

    return {
        "success": True,
        "message": "Payment verified successfully",
        "utr":     body.utr.strip(),
        "amount":  UPI_AMOUNT,
    }


@router.post("/verify-razorpay")
def verify_razorpay_payment(
    body: RazorpayVerifyRequest,
    current_user: dict = Depends(get_current_user),
):
    if not settings.RAZORPAY_KEY_SECRET:
        raise HTTPException(status_code=501, detail="Razorpay not configured")

    msg      = f"{body.razorpay_order_id}|{body.razorpay_payment_id}"
    expected = hmac.new(
        key=settings.RAZORPAY_KEY_SECRET.encode(),
        msg=msg.encode(),
        digestmod=hashlib.sha256,
    ).hexdigest()

    if expected != body.razorpay_signature:
        raise HTTPException(status_code=400, detail="Signature verification failed")

    payment = payment_collection.find_one({"loan_application_id": body.loan_application_id})
    if not payment:
        raise HTTPException(status_code=404, detail="Payment record not found")

    payment_collection.update_one(
        {"_id": payment["_id"]},
        {
            "$set": {
                "payment_completed":   True,
                "payment_id":          body.razorpay_payment_id,
                "razorpay_payment_id": body.razorpay_payment_id,
                "razorpay_signature":  body.razorpay_signature,
                "payment_amount":      float(UPI_AMOUNT),
                "payment_method":      "razorpay",
                "status":              "submitted",
                "submitted_at":        datetime.utcnow(),
            }
        },
    )

    return {"success": True, "message": "Razorpay payment verified"}


@router.get("/status/{loan_application_id}")
def payment_status(
    loan_application_id: str,
    current_user: dict = Depends(get_current_user),
):
    payment = payment_collection.find_one({"loan_application_id": loan_application_id})
    if not payment:
        return {"found": False, "payment_completed": False}

    return {
        "found":             True,
        "payment_completed": payment.get("payment_completed", False),
        "payment_id":        payment.get("payment_id"),
        "payment_amount":    payment.get("payment_amount"),
        "status":            payment.get("status"),
    }
