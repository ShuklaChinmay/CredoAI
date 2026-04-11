from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, Any
import requests

router = APIRouter(prefix="/chatbot", tags=["Chatbot"])


class ChatRequest(BaseModel):
    message: str
    session_id: str
    selected_loan: Optional[Any] = None
    username: Optional[str] = None


@router.post("/")
def chat(req: ChatRequest):
    try:
        response = requests.post(
            "http://127.0.0.1:9000/chat",
            json={
                "message": req.message,
                "session_id": req.session_id,
                "selected_loan": req.selected_loan,
                "username": req.username
            }
        )

        data = response.json()

        return {
            "reply": data.get("response"),
            "extra": data.get("extra"),
            "action": data.get("action")
        }

    except Exception as e:
        return {"reply": "Chatbot error", "error": str(e)}