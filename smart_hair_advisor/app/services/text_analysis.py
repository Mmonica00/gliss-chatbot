# app/services/text_analysis.py

import re

# ==============================
# 1️⃣ Hair texture extraction
# ==============================
def extract_hair_texture(text: str):
    """Detect hair texture: Fine / Medium / Coarse."""
    text = text.lower()
    if "fine" in text:
        return "Fine"
    elif "medium" in text:
        return "Medium"
    elif "coarse" in text:
        return "Coarse"
    return None


# ==============================
# 2️⃣ Hair type traits extraction
# ==============================
def extract_hair_type_traits(text: str):
    """
    Detect traits such as:
      - Greasy roots
      - Prone to split ends
      - Brittle
      - Strawy
      - Dry
      - Damaged
      - Colored 
      - Bleached
      - Normal
      - Dry tips
    """
    text = text.lower()

    traits = {
        "greasy_roots": any(word in text for word in ["greasy roots", "oily roots", "scalp is oily", "hair gets oily", "oily scalp", "greasy scalp"]),
        "split_ends": any(word in text for word in ["split ends", "ends are damaged", "split hair", "hair splits",]),
        "brittle": "brittle" in text or "breaks easily" in text,
        "strawy": "strawy" in text or "frizzy" in text or "rough" in text,
        "dry": any(word in text for word in ["dry hair", "hair is dry", "dryness", "dry scalp", "dry strands", "parched"]),
        "damaged": any(word in text for word in ["damaged hair", "hair is damaged", "damage", "damaging", "broken hair", "hair breakage"]),
        "colored": any(word in text for word in ["colored hair", "hair is colored", "color treated", "color damage", "coloring"]),
        "bleached": any(word in text for word in ["bleached hair", "hair is bleached", "bleach treated", "bleach damage", "bleaching"]),
        "normal": any(word in text for word in ["normal hair", "hair is normal", "not dry", "not oily"]),
        "dry_tips": any(word in text for word in ["dry tips", "tips are dry", "snappy ends", "dry ends", "dry split ends"])
    }

    # convert to list of dataset-style terms
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
    """
    Extract primary and secondary hair concerns.
    The mapping is designed to align with your dataset wording.
    """

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
        "greasy": "Oily scalp"
    }

    found = []
    for k, v in concern_map.items():
        if re.search(rf"\b{k}\b", text):
            found.append(v)

    found = list(dict.fromkeys(found))  # deduplicate while preserving order

    primary_concern = found[0] if len(found) > 0 else None
    secondary_concern = found[1] if len(found) > 1 else None

    return {"primary_concern": primary_concern, "secondary_concern": secondary_concern, "all_detected": found}


# ==============================
# 4️⃣ Unified function
# ==============================
def analyze_text_input(message: str):
    """
    Extract:
      - hair_texture
      - hair_type_keywords
      - primary_concern
      - secondary_concern
    """
    texture = extract_hair_texture(message)
    type_info = extract_hair_type_traits(message)
    concerns = extract_concerns(message)

    result = {
        "hair_texture": texture,
        "hair_type_keywords": type_info["hair_type_keywords"],
        "primary_concern": concerns["primary_concern"],
        "secondary_concern": concerns["secondary_concern"],
        "detected_concerns": concerns["all_detected"]
    }

    return result
