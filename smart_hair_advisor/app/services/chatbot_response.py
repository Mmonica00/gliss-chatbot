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
        # keep previous info unless new non-empty data provided
        if v:
            existing[k] = v
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

    # multiple product lines → ask clarification
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
    session_id: str = "default_session"
) -> Dict[str, Any]:
    """
    Conversational chatbot logic combining text + image analysis,
    accumulates user data until enough info is collected, then queries matcher.
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

    combined_hair_type = []
    seen = set()
    for token in hair_type_tokens:
        if token not in seen:
            seen.add(token)
            combined_hair_type.append(token)

    # --- Step 3.5: Fallback classification ---
    # If user said "dry", "damaged", or "colored" in text, infer hair_type when missing.
    text_lower = message.lower()
    fallback_hair_types = []
    if "dry" in text_lower:
        fallback_hair_types.append("dry")
    if "damage" in text_lower or "damaged" in text_lower:
        fallback_hair_types.append("damaged")
    if "color" in text_lower or "bleach" in text_lower:
        fallback_hair_types.append("colored & bleached")

    # Add only if hair_type_tokens is still empty
    if not hair_type_tokens and fallback_hair_types:
        hair_type_tokens.extend(fallback_hair_types)

    # --- Step 4: Merge with session memory ---
    user_profile = update_session(
        session_id,
        {
            "hair_type": combined_hair_type or None,
            "hair_texture": text_result.get("hair_texture"),
            "primary_concern": text_result.get("primary_concern"),
            "secondary_concern": text_result.get("secondary_concern"),
            "goal": text_result.get("goal"),
        },
    )

    # --- Step 5: Check required fields completeness ---
    required_fields = ["hair_type", "hair_texture", "primary_concern"]
    missing = [f for f in required_fields if not user_profile.get(f)]

    if missing:
        prompts = []
        if "hair_type" in missing:
            prompts.append("Could you tell me your hair type? (e.g., dry, damaged, or colored)")
        if "hair_texture" in missing:
            prompts.append("What’s your hair texture like — fine, thick, or wavy?")
        if "primary_concern" in missing:
            prompts.append("What’s your main concern right now — frizz, breakage, or dryness?")
        return {
            "message": " ".join(prompts),
            "need_more_info": True,
            "user_profile": sanitize(user_profile),
            "session_id": session_id,
        }

    # --- Step 6: Run matcher only when all required fields provided ---
    matches = match_user_profile(user_profile)
    if not matches:
        return {
            "message": (
                "I couldn’t find a confident match yet. "
                "Could you share a bit more about your goals — moisture, volume, or repair?"
            ),
            "need_more_info": True,
            "user_profile": sanitize(user_profile),
            "session_id": session_id,
        }

    normalized_matches = [{k.strip(): v for k, v in m.items()} for m in matches]
    top_score = normalized_matches[0].get("match_score", 0)
    threshold = 0.6

    if top_score < threshold:
        return {
            "message": (
                "Hmm, I'm not completely sure yet — could you tell me more about your goals? "
                "For example, do you want hydration, color protection, or repair?"
            ),
            "need_more_info": True,
            "user_profile": sanitize(user_profile),
            "matches": sanitize(normalized_matches),
            "session_id": session_id,
        }

    # --- Step 7: Evaluate matches (same product vs. clarify) ---
    evaluation = evaluate_matches(normalized_matches)
    evaluation.update({
        "user_profile": sanitize(user_profile),
        "matches": sanitize(normalized_matches),
        "session_id": session_id,
    })
    return evaluation
