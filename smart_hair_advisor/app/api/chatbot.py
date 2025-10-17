# app/api/chatbot.py
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form
from app.services.analysis import analyze_user_input
from app.services.text_analysis import analyze_text_input
from app.services.matcher import match_user_profile
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
async def analyze_hair(
    message: str = Form(...),
    image: Optional[UploadFile] = File(None)
):
    # analyze text always
    text_result = analyze_text_input(message)
    image_result = None
    hair_type_list = []

    # If image provided, analyze it
    if image:
        img_bytes = await image.read()
        image_result = analyze_user_input(img_bytes)

        # image_result may contain booleans from numpy — sanitize later
        # convert image interpretation keywords into simple trait tokens
        if isinstance(image_result, dict):
            # prefer hair_type_keywords if available (we added it in analysis.py)
            kws = image_result.get("hair_type_keywords")
            if kws:
                # Normalize to lower-case tokens for matcher
                hair_type_list.extend([str(k).lower() for k in kws])
            else:
                # fallback to interpretation strings -> keywords
                for interp in image_result.get("interpretation", []):
                    it = str(interp).lower()
                    if "dull" in it:
                        hair_type_list.append("dull")
                    if "dry" in it:
                        hair_type_list.append("dry")
                    if "color" in it or "bleach" in it:
                        hair_type_list.append("colored & bleached")
                    if "frizz" in it or "straw" in it or "texture" in it:
                        hair_type_list.append("strawy")
                    if "damage" in it or "split" in it:
                        hair_type_list.append("damaged")
                    if "long" in it:
                        hair_type_list.append("long hair")

    # Always include text-detected keywords
    text_keywords = text_result.get("hair_type_keywords", [])
    hair_type_list.extend([str(k).lower() for k in text_keywords])

    # remove duplicates while preserving order
    seen = set()
    combined_hair_type = []
    for item in hair_type_list:
        if item not in seen:
            seen.add(item)
            combined_hair_type.append(item)

    user_profile = {
        "hair_type": combined_hair_type,
        "hair_texture": text_result.get("hair_texture"),
        "primary_concern": text_result.get("primary_concern"),
        "secondary_concern": text_result.get("secondary_concern"),
    }

    matches = match_user_profile(user_profile)

    response = {
        "input_message": message,
        "hair_profile": user_profile,
        "text_analysis": text_result,
        "image_analysis": image_result,
        "matches": matches
    }

    # sanitize entire response recursively before returning
    return sanitize(response)
