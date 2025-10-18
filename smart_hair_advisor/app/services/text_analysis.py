import re

# ==============================
# 1️⃣ Hair texture extraction
# ==============================
def extract_hair_texture(text: str):
    text = text.lower()
    if "fine" in text:
        return "Fine"
    elif "medium" in text:
        return "Medium"
    elif "coarse" in text or "thick" in text:
        return "Coarse"
    elif "thin" in text:
        return "Fine"
    elif "wavy" in text:
        return "Medium"
    return None


# ==============================
# 2️⃣ Hair type traits extraction
# ==============================
def extract_hair_type_traits(text: str):
    text = text.lower()

    traits = {
        "greasy_roots": any(word in text for word in ["greasy roots", "oily roots", "scalp is oily", "oily scalp"]),
        "split_ends": any(word in text for word in ["split ends", "ends are damaged", "split hair"]),
        "brittle": "brittle" in text or "breaks easily" in text,
        "strawy": any(word in text for word in ["strawy", "frizzy", "rough"]),
        "dry": any(word in text for word in ["dry", "dryness"]),
        "damaged": any(word in text for word in ["damaged", "damage"]),
        "colored": any(word in text for word in ["colored", "color-treated", "dyed"]),
        "bleached": any(word in text for word in ["bleached", "bleach"]),
        "normal": "normal hair" in text,
        "dry_tips": any(word in text for word in ["dry tips", "dry ends"]),
    }

    keywords = []
    if traits["greasy_roots"]:
        keywords.append("Greasy roots")
    if traits["split_ends"]:
        keywords.append("Prone to split ends")
    if traits["brittle"]:
        keywords.append("Brittle")
    if traits["strawy"]:
        keywords.append("Strawy")
    if traits["dry"]:
        keywords.append("Dry")
    if traits["damaged"]:
        keywords.append("Damaged")
    if traits["colored"]:
        keywords.append("Colored")
    if traits["bleached"]:
        keywords.append("Bleached")
    if traits["normal"]:
        keywords.append("Normal")
    if traits["dry_tips"]:
        keywords.append("Dry tips")

    return {"traits": traits, "hair_type_keywords": keywords}


# ==============================
# 3️⃣ Concern extraction
# ==============================
def extract_concerns(text: str):
    text = text.lower()
    concern_map = {
        "dry": "Dryness",
        "damage": "Damaged hair",
        "breakage": "Breakage",
        "frizz": "Frizzy hair",
        "shine": "Lack of shine",
        "volume": "Lack of volume",
        "color": "Color protection",
        "bleach": "Colored & Bleached",
        "dandruff": "Scalp care",
        "hair fall": "Hair fall",
        "split": "Split ends",
        "smooth": "Smoothness",
        "repair": "Repair",
        "moisture": "Moisturizing",
        "hydration": "Moisturizing",
        "oily": "Oily scalp",
        "greasy": "Oily scalp",
    }

    found = []
    for k, v in concern_map.items():
        if re.search(rf"\b{k}\b", text):
            found.append(v)

    found = list(dict.fromkeys(found))
    primary_concern = found[0] if found else None
    secondary_concern = found[1] if len(found) > 1 else None

    return {
        "primary_concern": primary_concern,
        "secondary_concern": secondary_concern,
        "all_detected": found,
    }


# ==============================
# 4️⃣ Unified analyzer (SMART VERSION)
# ==============================
def analyze_text_input(user_input: str) -> dict:
    """
    Analyze text to extract hair attributes, concerns, and detect clarifications.
    """
    text = user_input.strip().lower()
    result = {
        "hair_type_keywords": [],
        "hair_texture": None,
        "primary_concern": None,
        "secondary_concern": None,
        "detected_concerns": [],
        "is_clarification": False,
    }

    # --- Detect clarification messages like “hydration”, “repair”, or “nourishment” ---
    clarification_keywords = ["hydration", "repair", "nourishment", "moisture", "dryness", "damage"]
    if text in clarification_keywords or any(word in text for word in clarification_keywords):
        result["is_clarification"] = True

    # --- Hair texture detection ---
    result["hair_texture"] = extract_hair_texture(text)

    # --- Hair type keywords ---
    for t in ["dry", "damaged", "colored", "bleached"]:
        if t in text:
            result["hair_type_keywords"].append(t.capitalize())

    # --- Concern detection ---
    concern_map = {
        "dry": "Dryness",
        "hydration": "Dryness",
        "moisture": "Dryness",
        "moisturizing": "Dryness",
        "frizz": "Frizz Control",
        "smooth": "Frizz Control",
        "shine": "Dullness",
        "dull": "Dullness",
        "repair": "Damage",
        "breakage": "Damage",
        "split": "Damage",
        "color": "Color Care",
        "nourish": "Nutrition",
        "nourishment": "Nutrition",
        "regeneration": "Damage",
    }

    for key, val in concern_map.items():
        if key in text:
            if not result["primary_concern"]:
                result["primary_concern"] = val
            elif val != result["primary_concern"]:
                result["secondary_concern"] = val
            result["detected_concerns"].append(val)

    return result