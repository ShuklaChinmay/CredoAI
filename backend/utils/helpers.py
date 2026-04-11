import math
import random
import string
import secrets
from datetime import datetime


def format_inr(amount: float) -> str:
    """Format number as Indian Rupees string."""
    if amount >= 10_000_000:
        return f"₹{amount / 10_000_000:.2f} Cr"
    if amount >= 100_000:
        return f"₹{amount / 100_000:.2f} L"
    return f"₹{amount:,.0f}"


def calculate_emi(principal: float, annual_rate: float, months: int) -> float:
    """Standard reducing balance EMI calculation."""
    if months <= 0 or principal <= 0:
        return 0.0
    r = annual_rate / 12 / 100
    if r == 0:
        return principal / months
    emi = principal * r * (1 + r) ** months / ((1 + r) ** months - 1)
    return round(emi, 2)


def generate_otp(length: int = 6) -> str:
    return "".join(secrets.choice(string.digits) for _ in range(length))


def generate_session_id() -> str:
    return secrets.token_hex(16)


def current_timestamp() -> str:
    return datetime.utcnow().isoformat()


def sanitise_phone(phone: str) -> str:
    import re
    digits = re.sub(r"\D", "", phone)
    if len(digits) == 10:
        return f"+91{digits}"
    if len(digits) == 12 and digits.startswith("91"):
        return f"+{digits}"
    return digits
