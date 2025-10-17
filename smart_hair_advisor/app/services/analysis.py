# app/services/analysis.py

from rembg import remove
from PIL import Image
import io, numpy as np
import cv2

def extract_hair_mask_bytes(image_bytes: bytes) -> np.ndarray:
    """Return binary mask (0/255) of hair/background using rembg (U2Net)."""
    result = remove(image_bytes)  # bytes -> bytes (PNG with alpha)
    img = Image.open(io.BytesIO(result)).convert("RGBA")
    alpha = np.array(img.split()[-1])  # extract alpha channel
    mask = (alpha > 0).astype("uint8") * 255
    return mask


def analyze_hair_features(image_bytes: bytes):
    """
    Analyze a hair image and extract explainable metrics + dataset-compatible traits.
    Returns:
        {
          "metrics": {...},
          "hair_type": {...},
          "hair_type_keywords": [...],
          "interpretation": [...]
        }
    """
    # 1. Extract mask and prepare image
    mask = extract_hair_mask_bytes(image_bytes)
    pil = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    img = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)

    # Apply mask
    hair_pixels = cv2.bitwise_and(img, img, mask=mask)
    hsv = cv2.cvtColor(hair_pixels, cv2.COLOR_BGR2HSV)
    v = hsv[:, :, 2]  # brightness
    s = hsv[:, :, 1]  # saturation

    hair_idx = mask > 0
    if hair_idx.sum() == 0:
        return {"error": "no hair detected"}

    # 2. Compute metrics
    brightness = int(v[hair_idx].mean())        # 0–255
    saturation = int(s[hair_idx].mean())        # 0–255
    gray = cv2.cvtColor(hair_pixels, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    edge_density = float(edges[hair_idx].sum() / 255) / hair_idx.sum()

    metrics = {
        "brightness": brightness,
        "saturation": saturation,
        "edge_density": edge_density
    }

    # 3. Infer traits (thresholds tuned heuristically)
    hair_type = {
        "dull": bool(brightness < 90),
        "dry": bool((saturation < 60) or (brightness < 80)),
        "colored_or_bleached": bool(saturation > 120),
        "long": bool((mask.sum() / 255) > 250000),  # approx. image area threshold
        "strawy": bool(edge_density > 0.08),
        "damaged": bool((edge_density > 0.1) or ((brightness < 80) and (saturation < 70)))
    }

    # 4. Map traits to dataset-compatible keywords
    keyword_map = {
        "dull": "Dull",
        "dry": "Dry",
        "colored_or_bleached": "Colored & Bleached",
        "long": "Long hair",
        "strawy": "Strawy",
        "damaged": "Damaged"
    }

    # Include only detected traits
    hair_type_keywords = [v for k, v in keyword_map.items() if hair_type[k]]

    # 5. Interpretations for user feedback
    interpretation = []
    if hair_type["dull"]:
        interpretation.append("Hair appears dull (low shine).")
    if hair_type["dry"]:
        interpretation.append("Hair appears dry — possible lack of moisture.")
    if hair_type["colored_or_bleached"]:
        interpretation.append("Hair color treated or bleached.")
    if hair_type["strawy"]:
        interpretation.append("Hair appears strawy — frizz or rough texture.")
    if hair_type["damaged"]:
        interpretation.append("Visible damage or split ends detected.")
    if hair_type["long"]:
        interpretation.append("Detected long hair length.")
    if not interpretation:
        interpretation.append("Hair looks healthy and balanced.")

    # 6. Return structured output
    return {
        "metrics": metrics,
        "hair_type": hair_type,
        "hair_type_keywords": hair_type_keywords,
        "interpretation": interpretation
    }


def analyze_user_input(image_bytes: bytes):
    """Compatibility wrapper for API usage."""
    return analyze_hair_features(image_bytes)
