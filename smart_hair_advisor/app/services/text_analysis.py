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
    elif "coarse" in text:
        return "Coarse"
    elif "thick" in text:
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
def analyze_text_input(message: str):
    text = message.lower().strip()

    texture = extract_hair_texture(text)
    type_info = extract_hair_type_traits(text)
    concerns = extract_concerns(text)

    hair_type_keywords = type_info["hair_type_keywords"][:]

    # --- Smarter direct keyword capture ---
    # Catch hair type directly from text if missed
    if not hair_type_keywords:
        if any(word in text for word in ["dry", "dryness", "frizzy", "rough"]):
            hair_type_keywords.append("Dry")
        if any(word in text for word in ["damaged", "breakage", "broken"]):
            hair_type_keywords.append("Damaged")
        if any(word in text for word in ["colored", "color-treated", "dyed", "bleached"]):
            hair_type_keywords.append("Colored & Bleached")

    # Catch texture from descriptive words if missed
    if not texture:
        if any(word in text for word in ["fine", "thin", "delicate"]):
            texture = "Fine"
        elif any(word in text for word in ["medium", "normal"]):
            texture = "Medium"
        elif any(word in text for word in ["coarse", "thick", "dense", "wavy", "curly"]):
            texture = "Coarse"

    # If hydration/moisture mentioned but no dryness detected
    if "Moisturizing" in concerns["all_detected"] and "Dry" not in hair_type_keywords:
        hair_type_keywords.append("Dry")

    # If color/bleach mentioned, ensure color concern consistency
    if any(k in text for k in ["color", "bleach", "dyed"]) and "Color protection" not in concerns["all_detected"]:
        concerns["all_detected"].append("Color protection")

    result = {
        "hair_texture": texture,
        "hair_type_keywords": list(dict.fromkeys(hair_type_keywords)),  # remove duplicates
        "primary_concern": concerns["primary_concern"],
        "secondary_concern": concerns["secondary_concern"],
        "detected_concerns": concerns["all_detected"],
    }

    return result
