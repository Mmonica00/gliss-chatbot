# app/services/matcher.py
import os
import pandas as pd
import numpy as np
import re
from typing import Dict, Any, List

# Cache dataset after first load
_DATASET = None

def load_dataset(dataset_path=None):
    """Load the Hackathon dataset safely, regardless of where the app runs."""
    global _DATASET
    if _DATASET is not None:
        return _DATASET

    base_dir = os.path.dirname(os.path.abspath(__file__))
    if dataset_path is None:
        dataset_path = os.path.join(base_dir, "../data/Hackathon_dataset.xlsx")

    dataset_path = os.path.normpath(dataset_path)
    print(f"📘 Loading dataset from: {dataset_path}")

    if not os.path.exists(dataset_path):
        raise FileNotFoundError(f"❌ Dataset not found at: {dataset_path}")

    _DATASET = pd.read_excel(dataset_path)
    return _DATASET


def tokenize(value: str):
    """Split comma-separated or space-separated traits into a list."""
    if not value:
        return []
    return re.split(r"[,/]| and | or |;", str(value).lower())


def compute_similarity(user_traits: List[str], dataset_traits: List[str]) -> float:
    """Return Jaccard similarity between two sets."""
    if not user_traits or not dataset_traits:
        return 0.0
    user_set = set(t.strip() for t in user_traits if t.strip())
    data_set = set(t.strip() for t in dataset_traits if t.strip())
    intersection = len(user_set & data_set)
    union = len(user_set | data_set)
    return intersection / union if union > 0 else 0.0


def _to_serializable(value):
    """Convert numpy/pandas types to native python types for JSON safety."""
    # pandas / numpy scalar
    if isinstance(value, (np.generic,)):
        try:
            return value.item()
        except Exception:
            return str(value)
    # pandas NA
    if pd.isna(value):
        return None
    # pandas Timestamp
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    # anything else — convert bytes->str, otherwise return as-is (str for objects)
    if isinstance(value, (bytes, bytearray)):
        try:
            return value.decode("utf-8", errors="ignore")
        except Exception:
            return str(value)
    return value


def match_user_profile(user_data: Dict[str, Any], top_n: int = 3):
    """
    Match user data to the best fitting profiles in the dataset.

    user_data example:
    {
        "hair_type": ["dry", "damaged", "strawy"],
        "hair_texture": "fine",
        "primary_concern": "Dryness",
        "secondary_concern": "Frizzy hair"
    }
    """
    df = load_dataset()
    results = []

    for _, row in df.iterrows():
        hair_type_sim = compute_similarity(
            user_data.get("hair_type", []),
            tokenize(row.get("Hair Type", ""))
        )
        texture_sim = 1.0 if str(user_data.get("hair_texture", "")).lower() in str(row.get("Hair Texture", "")).lower() else 0.0
        primary_sim = 1.0 if str(user_data.get("primary_concern", "")).lower() in str(row.get("Primary Concern", "")).lower() else 0.0
        secondary_sim = 1.0 if str(user_data.get("secondary_concern", "")).lower() in str(row.get("Secondary Concern", "")).lower() else 0.0

        total_score = (0.4 * hair_type_sim) + (0.2 * texture_sim) + (0.25 * primary_sim) + (0.15 * secondary_sim)

        # convert every cell to JSON-safe python types
        clean_row = {k: _to_serializable(v) for k, v in row.to_dict().items()}

        results.append({
            "match_score": float(round(total_score, 3)),
            **clean_row
        })

    ranked = sorted(results, key=lambda x: x["match_score"], reverse=True)
    top_matches = [r for r in ranked[:top_n] if r["match_score"] > 0]

    return top_matches
