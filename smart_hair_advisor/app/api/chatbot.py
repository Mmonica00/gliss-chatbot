# app/api/chatbot.py
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form
from app.services.chatbot_response import generate_chatbot_response
import numpy as np
import pandas as pd

router = APIRouter(prefix="/chatbot", tags=["Chatbot"])

def _sanitize_value(v):
    """Convert numpy/pandas scalars recursively to python types."""
    # NumPy scalar
    if isinstance(v, (np.generic,)):
        try:
            return v.item()
        except Exception:
            return v.tolist() if hasattr(v, "tolist") else v
    # pandas NA
    if pd.isna(v):
        return None
    # dict/list: recurse
    if isinstance(v, dict):
        return {k: _sanitize_value(val) for k, val in v.items()}
    if isinstance(v, list):
        return [_sanitize_value(i) for i in v]
    # other types: return as-is
    return v

def sanitize(obj):
    """Recursively sanitize common containers to be JSON serializable."""
    if isinstance(obj, dict):
        return {k: sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [sanitize(v) for v in obj]
    return _sanitize_value(obj)


@router.post("/analyze")
async def analyze_chatbot_input(
    message: Optional[str] = Form(None, description="User text input"),
    image: Optional[UploadFile] = File(None, description="Optional hair image"),
    session_id: Optional[str] = Form("default_session", description="Session ID for ongoing chat")
):
    image_bytes = await image.read() if image else None

    # Defensive check — must provide either text or image
    if not message and not image_bytes:
        return {
            "error": "Please provide either a text message or an image for analysis."
        }

    # Call the unified chatbot logic
    response = generate_chatbot_response(
        message=message or "",
        image_bytes=image_bytes,
        session_id=session_id
    )

    return response