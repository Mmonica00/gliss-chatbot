from typing import Dict, Any, Optional
from app.services.analysis import analyze_user_input
from app.services.text_analysis import analyze_text_input
from app.services.matcher import match_user_profile
import numpy as np
import pandas as pd
import uuid
import time

# --- Configurable constants ---
SESSION_TIMEOUT = 600  # 10 minutes

# Session memory storage
SESSION_MEMORY: Dict[str, Dict[str, Any]] = {}


# --- Utility: JSON sanitization ---
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


# --- Session management ---
def reset_sessions():
    """Clear all stored user sessions."""
    SESSION_MEMORY.clear()
    print("🧹 All sessions have been reset.")

def generate_session_id() -> str:
    """Generate a new random session ID."""
    return str(uuid.uuid4())

def _is_session_expired(session_id: str) -> bool:
    """Check if a session exists and is still active."""
    session_data = SESSION_MEMORY.get(session_id)
    if not session_data:
        return True
    last_activity = session_data.get("_last_activity", 0)
    return (time.time() - last_activity) > SESSION_TIMEOUT

def _refresh_session_timestamp(session_id: str):
    """Update last activity time."""
    if session_id in SESSION_MEMORY:
        SESSION_MEMORY[session_id]["_last_activity"] = time.time()

def get_or_create_session(session_id: Optional[str]) -> str:
    """Return a valid session, regenerating if expired."""
    if not session_id or _is_session_expired(session_id):
        new_id = generate_session_id()
        SESSION_MEMORY[new_id] = {"_last_activity": time.time()}
        print(f"🆕 New session created: {new_id}")
        return new_id
    _refresh_session_timestamp(session_id)
    return session_id


# --- Session update helper ---
def update_session(session_id: str, new_data: Dict[str, Any]) -> Dict[str, Any]:
    """Merge new user data into existing session."""
    if _is_session_expired(session_id):
        print(f"⚠️ Session {session_id} expired. Creating a new one.")
        session_id = generate_session_id()
        SESSION_MEMORY[session_id] = {}

    existing = SESSION_MEMORY.get(session_id, {})
    for k, v in new_data.items():
        if v is not None and v != [] and v != "":
            existing[k] = v

    existing["_last_activity"] = time.time()
    SESSION_MEMORY[session_id] = existing
    return existing


# --- Match evaluator ---
def evaluate_matches(matches):
    if not matches:
        return {"message": "I couldn’t find a confident match yet."}

    normalized = [{k.strip(): v for k, v in m.items()} for m in matches]
    top_products = list({m.get("Product") for m in normalized if m.get("Product")})
    if not top_products:
        return {"message": "Sorry, no recognizable products found in matches."}

    if len(top_products) == 1:
        product = top_products[0]
        combined_steps = [m for m in normalized if m.get("Product") == product]
        return {
            "message": f"I recommend the **{product}** range. It includes:",
            "combined_recommendations": sanitize(combined_steps),
            "final_recommendation": True,
        }

    products = ", ".join(top_products)
    return {
        "message": f"I found strong matches for {products}. Which goal is more important — repair, hydration, or nourishment?",
        "need_clarification": True,
        "options": top_products,
    }


# --- Core chatbot logic ---
def generate_chatbot_response(
    message: str,
    image_bytes: Optional[bytes] = None,
    session_id: Optional[str] = None
) -> Dict[str, Any]:
    """Main conversational logic for chatbot."""

    # Ensure session validity
    session_id = get_or_create_session(session_id)
    print(f"⚙️ Chatbot invoked | Session: {session_id}")

    # --- Step 1: Analyze text ---
    text_result = analyze_text_input(message)
    print("Text analysis result:", text_result)

    # --- Step 2: Analyze optional image ---
    image_result = None
    hair_type_tokens = []
    if image_bytes:
        image_result = analyze_user_input(image_bytes)
        print("Image analysis result:", image_result)
        if isinstance(image_result, dict):
            kws = image_result.get("hair_type_keywords") or []
            hair_type_tokens.extend([str(k).lower() for k in kws])

    # --- Step 3: Merge text + image keywords ---
    text_keywords = [str(k).lower() for k in text_result.get("hair_type_keywords", [])]
    hair_type_tokens.extend(text_keywords)
    combined_hair_type = list(dict.fromkeys(hair_type_tokens))

    # --- Step 3.5: Fallbacks ---
    text_lower = message.lower()
    if not combined_hair_type:
        if "dry" in text_lower:
            combined_hair_type.append("dry")
        if "damage" in text_lower or "damaged" in text_lower:
            combined_hair_type.append("damaged")
        if "color" in text_lower or "bleach" in text_lower:
            combined_hair_type.append("colored & bleached")

    # --- Step 4: Merge into session ---
    user_profile = update_session(
        session_id,
        {
            "hair_type": combined_hair_type or None,
            "hair_texture": text_result.get("hair_texture"),
            "primary_concern": text_result.get("primary_concern"),
            "secondary_concern": text_result.get("secondary_concern"),
        },
    )
    print("🧠 Merged user profile:", user_profile)

    # --- Step 5: Check completeness ---
    required_fields = ["hair_type", "hair_texture", "primary_concern"]
    missing = [f for f in required_fields if not user_profile.get(f)]

    # --- Prevent infinite re-asking of same question ---
    if missing:
        if user_profile.get("_last_asked") == missing:
            return {
                "message": "I’m still not sure — could you describe your hair in a bit more detail?",
                "need_more_info": True,
                "user_profile": sanitize(user_profile),
                "session_id": session_id,
            }
        user_profile["_last_asked"] = missing

        prompts = []
        if "hair_type" in missing:
            prompts.append("Could you tell me your hair type? (e.g., dry, damaged, or colored)")
        if "hair_texture" in missing:
            prompts.append("What’s your hair texture like — fine, medium, or coarse?")
        if "primary_concern" in missing:
            prompts.append("What’s your main concern — frizz, dryness, or repair?")

        return {
            "message": " ".join(prompts),
            "need_more_info": True,
            "user_profile": sanitize(user_profile),
            "session_id": session_id,
        }

    # --- Step 6: Match evaluation ---
    matches = match_user_profile(user_profile)
    if not matches:
        return {
            "message": "I couldn’t find a confident match yet. Could you share more about your goals — moisture, volume, or repair?",
            "need_more_info": True,
            "user_profile": sanitize(user_profile),
            "session_id": session_id,
        }

    normalized_matches = [{k.strip(): v for k, v in m.items()} for m in matches]
    top_score = normalized_matches[0].get("match_score", 0)

    if top_score < 0.6:
        return {
            "message": "Hmm, I'm not completely sure yet — could you tell me more about your goals? For example, do you want hydration, color protection, or repair?",
            "need_more_info": True,
            "user_profile": sanitize(user_profile),
            "matches": sanitize(normalized_matches),
            "session_id": session_id,
        }

    # --- Step 7: Final recommendation ---
    evaluation = evaluate_matches(normalized_matches)
    evaluation.update({
        "user_profile": sanitize(user_profile),
        "matches": sanitize(normalized_matches),
        "session_id": session_id,
    })
    return evaluation