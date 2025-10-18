from typing import Dict, Any, Optional
from app.services.analysis import analyze_user_input
from app.services.text_analysis import analyze_text_input
from app.services.matcher import match_user_profile
import numpy as np
import pandas as pd
import uuid
import time

SESSION_TIMEOUT = 600  # 10 minutes
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
    SESSION_MEMORY.clear()
    print("🧹 All sessions have been reset.")

def generate_session_id() -> str:
    return str(uuid.uuid4())

def _is_session_expired(session_id: str) -> bool:
    session_data = SESSION_MEMORY.get(session_id)
    if not session_data:
        return True
    last_activity = session_data.get("_last_activity", 0)
    return (time.time() - last_activity) > SESSION_TIMEOUT

def _refresh_session_timestamp(session_id: str):
    if session_id in SESSION_MEMORY:
        SESSION_MEMORY[session_id]["_last_activity"] = time.time()

def get_or_create_session(session_id: Optional[str]) -> str:
    if not session_id or _is_session_expired(session_id):
        new_id = generate_session_id()
        SESSION_MEMORY[new_id] = {"_last_activity": time.time()}
        print(f"🆕 New session created: {new_id}")
        return new_id
    _refresh_session_timestamp(session_id)
    return session_id

# --- Session update helper ---
def update_session(session_id: str, new_data: Dict[str, Any]) -> Dict[str, Any]:
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
        return {"message": "Hmm, I'm having a bit of trouble finding the perfect match for you right now. Could you tell me a bit more about your hair?"}

    normalized = [{k.strip(): v for k, v in m.items()} for m in matches]
    top_products = list({m.get("Product") for m in normalized if m.get("Product")})
    if not top_products:
        return {"message": "Oops! I couldn't find any products that match your needs. Let me try to help you better!"}

    if len(top_products) == 1:
        product = top_products[0]
        combined_steps = [m for m in normalized if m.get("Product") == product]
        return {
            "message": f"Perfect! I've found just the right solution for you. I recommend the **{product}** range — it's exactly what your hair needs! Here's what it includes:",
            "combined_recommendations": sanitize(combined_steps),
            "final_recommendation": True,
        }

    products = ", ".join(top_products)
    return {
        "message": f"Great news! I found some fantastic matches for you: {products}. To give you the best recommendation, could you help me understand which goal is most important to you — repair, hydration, or nourishment?",
        "need_clarification": True,
        "options": top_products,
    }

# --- Core chatbot logic ---
def generate_chatbot_response(
    message: str,
    image_bytes: Optional[bytes] = None,
    session_id: Optional[str] = None
) -> Dict[str, Any]:
    session_id = get_or_create_session(session_id)
    print(f"⚙️ Chatbot invoked | Session: {session_id}")

    matches = []

    # --- Step 1: Text analysis ---
    text_result = analyze_text_input(message)
    print("Text analysis result:", text_result)

    # --- Step 2: Optional image analysis ---
    image_result = None
    hair_type_tokens = []
    if image_bytes:
        image_result = analyze_user_input(image_bytes)
        print("Image analysis result:", image_result)
        if isinstance(image_result, dict):
            kws = image_result.get("hair_type_keywords") or []
            hair_type_tokens.extend([str(k).lower() for k in kws])

    # --- Step 3: Merge hair keywords from text ---
    text_keywords = [str(k).lower() for k in text_result.get("hair_type_keywords", [])]
    hair_type_tokens.extend(text_keywords)
    combined_hair_type = list(dict.fromkeys(hair_type_tokens))

    # --- Step 4: Basic fallback detection from text ---
    text_lower = message.lower()

    need_clarification = False
    if not text_result.get("is_clarification") and not any(
        k in text_lower for k in ["hydration", "repair", "nourishment"]
    ):
        need_clarification = True


    if not combined_hair_type:
        if "dry" in text_lower:
            combined_hair_type.append("dry")
        if "damage" in text_lower or "damaged" in text_lower:
            combined_hair_type.append("damaged")
        if "color" in text_lower or "bleach" in text_lower:
            combined_hair_type.append("colored & bleached")

    # --- Step 5: Normalize concern synonyms ---
    concern_synonyms = {
        "hydration": "Dryness",
        "moisture": "Dryness",
        "moisturizing": "Dryness",
        "repair": "Damage",
        "regeneration": "Damage",
        "shine": "Dullness",
        "smooth": "Frizz Control",
        "color protection": "Color Care",
        "nourishment": "Nutrition",
    }

    normalized_concern = text_result.get("primary_concern")
    for key, value in concern_synonyms.items():
        if key in text_lower:
            normalized_concern = value
            break

    # --- Step 6: Handle clarification replies (user says: "hydration", "repair", etc.) ---
    if text_result.get("is_clarification") or any(k in text_lower for k in ["hydration", "repair", "nourishment"]):
        print("🧩 Detected clarification intent.")
        if "hydration" in text_lower or "moisturizing" in text_lower:
            normalized_concern = "Dryness"
        elif "repair" in text_lower:
            normalized_concern = "Damage"
        elif "nourishment" in text_lower or "nutrition" in text_lower:
            normalized_concern = "Nutrition"

    # --- Step 7: Merge profile in session ---
    user_profile = update_session(
        session_id,
        {
            "hair_type": combined_hair_type or None,
            "hair_texture": text_result.get("hair_texture"),
            "primary_concern": normalized_concern,
            "secondary_concern": text_result.get("secondary_concern"),
        },
    )
    print("🧠 Merged user profile:", user_profile)

    # --- Step 8: Check required fields ---
    required_fields = ["hair_type", "hair_texture", "primary_concern"]
    has_all_info = all(user_profile.get(f) for f in required_fields)

    if not has_all_info:
        missing = [f for f in required_fields if not user_profile.get(f)]
        if user_profile.get("_last_asked") == missing:
            return {
                "message": "I'd love to help you find the perfect hair care solution! Could you tell me a bit more about your hair so I can give you the best recommendation?",
                "need_more_info": True,
                "user_profile": sanitize(user_profile),
                "session_id": session_id,
            }
        user_profile["_last_asked"] = missing

        prompts = []
        if "hair_type" in missing:
            prompts.append("What's your hair type like? (e.g., dry, damaged, or colored)")
        if "hair_texture" in missing:
            prompts.append("How would you describe your hair texture — fine, medium, or coarse?")
        if "primary_concern" in missing:
            prompts.append("What's your main hair concern — frizz, dryness, or repair?")

        return {
            "message": " ".join(prompts),
            "need_more_info": True,
            "user_profile": sanitize(user_profile),
            "session_id": session_id,
        }

    # --- ✅ Step 9: Always assign matches before using them ---
    matches = match_user_profile(user_profile)

    if not matches:
        return {
            "message": "I'm having a bit of trouble finding the perfect match for you. Could you tell me more about your hair goals — are you looking for moisture, volume, or repair?",
            "need_more_info": True,
            "user_profile": sanitize(user_profile),
            "session_id": session_id,
        }

    # --- Step 10: Evaluate matches ---
    normalized_matches = [{k.strip(): v for k, v in m.items()} for m in matches]
    top_score = normalized_matches[0].get("match_score", 0)

    # --- Step 11: Low-confidence fallback ---
    if top_score < 0.6 and not user_profile.get("primary_concern"):
        return {
            "message": "I want to make sure I give you the perfect recommendation! Could you tell me more about your hair goals? For example, are you looking for hydration, color protection, or repair?",
            "need_more_info": True,
            "user_profile": sanitize(user_profile),
            "matches": sanitize(normalized_matches),
            "session_id": session_id,
        }

   # --- Step 12: Clarification cycle control ---
    evaluation = evaluate_matches(normalized_matches)

    # Use flag to control clarification behavior
    if not need_clarification:
        evaluation["need_clarification"] = False


    # Prevent repeated looping if clarification was already given
    if text_result.get("is_clarification") or any(k in text_lower for k in ["hydration", "repair", "nourishment"]):
        evaluation["need_clarification"] = False
        
        # Filter matches based on clarification
        if "hydration" in text_lower or "moisturizing" in text_lower:
            # Prefer Aqua Revive for hydration
            filtered_matches = [m for m in normalized_matches if m.get("Product") == "Aqua Revive"]
            if filtered_matches:
                normalized_matches = filtered_matches
        elif "repair" in text_lower:
            # Prefer Total Repair for repair
            filtered_matches = [m for m in normalized_matches if m.get("Product") == "Total Repair"]
            if filtered_matches:
                normalized_matches = filtered_matches
        elif "nourishment" in text_lower or "nutrition" in text_lower:
            # Prefer products with nutrition focus
            filtered_matches = [m for m in normalized_matches if "Nutrition" in str(m.get("Primary Concern", "")) or "Nutrition" in str(m.get("Secondary Concern", ""))]
            if filtered_matches:
                normalized_matches = filtered_matches
        
        # Re-evaluate with filtered matches
        if normalized_matches:
            evaluation = evaluate_matches(normalized_matches)
            evaluation["need_clarification"] = False
            evaluation["final_recommendation"] = True

    # --- Step 13: Return response ---
    evaluation.update({
        "user_profile": sanitize(user_profile),
        "matches": sanitize(normalized_matches),
        "session_id": session_id,
    })

    return evaluation
