from typing import Dict, Any, Optional
from app.services.analysis import analyze_user_input
from app.services.text_analysis import analyze_text_input
from app.services.matcher import match_user_profile
import numpy as np
import pandas as pd

# Session memory to persist user profile across conversation turns
SESSION_MEMORY: Dict[str, Dict[str, Any]] = {}


# --- Utility: clean values for JSON responses ---
def _sanitize_value(v):
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
    if isinstance(obj, dict):
        return {k: sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [sanitize(v) for v in obj]
    return _sanitize_value(obj)


# --- Session update helper ---
def update_session(session_id: str, new_data: Dict[str, Any]) -> Dict[str, Any]:
    existing = SESSION_MEMORY.get(session_id, {})
    for k, v in new_data.items():
        if v:  # only overwrite with non-empty values
            existing[k] = v
    SESSION_MEMORY[session_id] = existing
    return existing


# --- Core chatbot logic ---
def generate_chatbot_response(
    message: str,
    image_bytes: Optional[bytes] = None,
    session_id: str = "default_session"
) -> Dict[str, Any]:
    """
    Handles chat interactions combining text + image analysis,
    keeps context (session memory), and queries matcher for product recommendations.
    """

    print("⚙️ Chatbot invoked | Text + Image input merge in progress...")

    # --- Step 1: Analyze text ---
    text_result = analyze_text_input(message)
    print("Text analysis result:", text_result)

    # --- Step 2: Analyze image (if any) ---
    image_result = None
    hair_type_tokens = []
    if image_bytes:
        image_result = analyze_user_input(image_bytes)
        print("Image analysis result:", image_result)
        if isinstance(image_result, dict):
            kws = image_result.get("hair_type_keywords") or []
            hair_type_tokens.extend([str(k).lower() for k in kws])
        else:
            # fallback: parse free text interpretation list
            for interp in image_result.get("interpretation", []):
                text = str(interp).lower()
                if "dry" in text:
                    hair_type_tokens.append("dry")
                if "damage" in text:
                    hair_type_tokens.append("damaged")
                if "color" in text or "bleach" in text:
                    hair_type_tokens.append("colored & bleached")
                if "frizz" in text or "straw" in text:
                    hair_type_tokens.append("strawy")
                if "split" in text:
                    hair_type_tokens.append("split ends")
                if "long" in text:
                    hair_type_tokens.append("long hair")

    # --- Step 3: Merge text + image ---
    text_keywords = text_result.get("hair_type_keywords", [])
    hair_type_tokens.extend([str(k).lower() for k in text_keywords])

    # Deduplicate tokens
    combined_hair_type = []
    seen = set()
    for token in hair_type_tokens:
        if token not in seen:
            seen.add(token)
            combined_hair_type.append(token)

    # --- Step 4: Merge with session memory ---
    user_profile = update_session(
        session_id,
        {
            "hair_type": combined_hair_type or None,
            "hair_texture": text_result.get("hair_texture"),
            "primary_concern": text_result.get("primary_concern"),
            "secondary_concern": text_result.get("secondary_concern"),
        },
    )

    # --- Step 5: Check missing info ---
    missing_fields = [k for k, v in user_profile.items() if not v]
    if missing_fields:
        ask = []
        if "hair_type" in missing_fields:
            ask.append("Could you describe your hair type? For example, dry, damaged, or colored?")
        if "hair_texture" in missing_fields:
            ask.append("What’s your hair texture like — fine, thick, or wavy?")
        if "primary_concern" in missing_fields:
            ask.append("What’s your main hair concern right now — frizz, breakage, or dryness?")
        return {
            "message": " ".join(ask),
            "need_more_info": True,
            "user_profile": sanitize(user_profile),
            "session_id": session_id
        }

    # --- Step 6: Match profile ---
    matches = match_user_profile(user_profile)
    if not matches:
        return {
            "message": (
                "I couldn’t find a confident match yet. "
                "Could you share a bit more about what your hair needs — moisture, volume, or repair?"
            ),
            "need_more_info": True,
            "user_profile": sanitize(user_profile),
            "session_id": session_id
        }

    # Normalize and clean matches
    normalized_matches = [{k.strip(): v for k, v in m.items()} for m in matches]
    top_score = normalized_matches[0].get("match_score", 0)
    top_products = list({m.get("Product") for m in normalized_matches if m.get("Product")})
    threshold = 0.6

    # --- Step 7: Build conversational response ---
    if top_score < threshold:
        return {
            "message": (
                "Hmm, I'm not completely sure yet — could you tell me more about your goals? "
                "For example, do you want hydration, color protection, or repair?"
            ),
            "need_more_info": True,
            "user_profile": sanitize(user_profile),
            "matches": sanitize(normalized_matches),
            "session_id": session_id
        }

    if len(top_products) == 1:
        product = top_products[0]
        traits = ", ".join(user_profile.get("hair_type", []))
        concern = user_profile.get("primary_concern", "general care")
        response_text = (
            f"From what I can tell, your hair seems to be {traits}. "
            f"For {concern}, I’d recommend the **{product}** line.\n\n"
            "It’s gentle yet effective — it cleanses without stripping, "
            "and strengthens the strands over time. "
            "Used together, it helps your hair feel softer, stronger, and easier to manage."
        )
        return {
            "message": response_text,
            "need_more_info": False,
            "user_profile": sanitize(user_profile),
            "matches": sanitize(normalized_matches),
            "session_id": session_id
        }

    # multiple options
    options = " or ".join(top_products[:2])
    response_text = (
        f"I found a few good options that could suit you: {options}. "
        "Would you say your main goal is repair, hydration, or volume? That’ll help me fine-tune the choice."
    )
    return {
        "message": response_text,
        "need_more_info": True,
        "user_profile": sanitize(user_profile),
        "matches": sanitize(normalized_matches),
        "session_id": session_id
    }
