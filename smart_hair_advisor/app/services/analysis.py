# app/services/hair_photo.py
from rembg import remove
from PIL import Image
import io, numpy as np
import cv2

def extract_hair_mask_bytes(image_bytes: bytes) -> np.ndarray:
    """Return binary mask (0/255) of hair/background using rembg (U2Net)."""
    # rembg returns RGBA with alpha where foreground is preserved
    result = remove(image_bytes)  # bytes -> bytes (PNG/PNG with alpha)
    img = Image.open(io.BytesIO(result)).convert("RGBA")
    alpha = np.array(img.split()[-1])  # alpha channel
    mask = (alpha > 0).astype("uint8") * 255
    return mask

def analyze_hair_features(image_bytes: bytes):
    """
    Returns simple explainable metrics:
      - brightness (0-255)
      - saturation (0-255)
      - edge_density (0-1)
    """
    # Get hair mask
    mask = extract_hair_mask_bytes(image_bytes)

    # Load original image as BGR numpy
    pil = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    img = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)

    # Apply mask: keep hair pixels only
    hair_pixels = cv2.bitwise_and(img, img, mask=mask)

    # Convert to HSV for brightness/saturation
    hsv = cv2.cvtColor(hair_pixels, cv2.COLOR_BGR2HSV)
    v = hsv[:,:,2]
    s = hsv[:,:,1]

    # compute numeric stats only on hair pixels (mask>0)
    hair_idx = mask > 0
    if hair_idx.sum() == 0:
        return {"error": "no hair detected"}

    brightness = int(v[hair_idx].mean())        # 0-255
    saturation = int(s[hair_idx].mean())        # 0-255

    # Edge density (Canny)
    gray = cv2.cvtColor(hair_pixels, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    edge_density = float(edges[hair_idx].sum() / 255) / hair_idx.sum()  # fraction of hair pixels that are edges

    # Rough heuristics mapping
    heuristics = {}
    heuristics['brightness'] = brightness
    heuristics['saturation'] = saturation
    heuristics['edge_density'] = edge_density

    # Interpretations (tune thresholds)
    interpretations = []
    if brightness < 80:
        interpretations.append("Dullness / Dryness")
    if saturation < 50:
        interpretations.append("Color Fading / Damage")
    if edge_density > 0.08:  # threshold, tune with examples
        interpretations.append("Frizz / High Texture")
    if not interpretations:
        interpretations.append("Healthy / No major issues detected")

    return {"metrics": heuristics, "interpretation": interpretations}

# Add compatibility wrapper expected by the API:
def analyze_user_input(image_bytes: bytes):
    """
    Compatibility wrapper for older API name.
    Delegates to analyze_hair_features.
    """
    return analyze_hair_features(image_bytes)
