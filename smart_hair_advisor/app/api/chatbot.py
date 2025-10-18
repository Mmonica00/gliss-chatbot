# app/api/chatbot.py
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form
from app.services.chatbot_response import (
    generate_chatbot_response,
    generate_session_id,   # <-- new import
    reset_sessions         # optional import if you want to expose reset endpoint
)
import numpy as np
import pandas as pd

router = APIRouter(prefix="/chatbot", tags=["Chatbot"])


# --- Utility sanitization helpers (same as before) ---
def _sanitize_value(v):
    """Convert numpy/pandas scalars recursively to python types."""
    if isinstance(v, (np.generic,)):
        try:
            return v.item()
        except Exception:
            return v.tolist() if hasattr(v, "tolist") else v
    if pd.isna(v):
        return None
    if isinstance(v, dict):
        return {k: _sanitize_value(val) for k, val in v.items()}
    if isinstance(v, list):
        return [_sanitize_value(i) for i in v]
    return v


def sanitize(obj):
    """Recursively sanitize common containers to be JSON serializable."""
    if isinstance(obj, dict):
        return {k: sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [sanitize(v) for v in obj]
    return _sanitize_value(obj)


# --- Main chatbot endpoint ---
@router.post("/analyze")
async def analyze_chatbot_input(
    message: Optional[str] = Form(None, description="User text input"),
    image: Optional[UploadFile] = File(None, description="Optional hair image"),
    session_id: Optional[str] = Form(None, description="Session ID for ongoing chat")
):
    """
    Unified chatbot entry point — handles text and image input.
    Automatically manages session lifecycle and expiry.
    """
    image_bytes = await image.read() if image else None

    # Defensive check — must provide either text or image
    if not message and not image_bytes:
        return {
            "error": "Please provide either a text message or an image for analysis."
        }

    # If no session ID provided (e.g., user reloaded the site) → generate new one
    if not session_id or session_id == "default_session":
        session_id = generate_session_id()
        print(f"🆕 New session generated on frontend reload: {session_id}")

    # Run chatbot logic
    response = generate_chatbot_response(
        message=message or "",
        image_bytes=image_bytes,
        session_id=session_id
    )

    # Ensure the session_id is always returned for frontend continuity
    if "session_id" not in response:
        response["session_id"] = session_id

    return sanitize(response)


# --- Optional: Admin/Debug Endpoint ---
@router.post("/reset")
async def reset_all_sessions():
    """Manually clear all session data (useful for admin/debugging)."""
    reset_sessions()
    return {"message": "All chatbot sessions have been cleared."}