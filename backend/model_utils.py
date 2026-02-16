# backend/model_utils.py

from pathlib import Path
from typing import Dict, Literal

import joblib
import numpy as np

# -----------------------------
# Types
# -----------------------------
Label = Literal["low", "medium", "high"]
PriorityLabel = Literal["low", "medium", "high", "critical"]

DIMENSIONS = ["severity", "urgency", "impact"]

LABEL_TO_SCORE = {
    "low": 1,
    "medium": 2,
    "high": 3,
}

# -----------------------------
# Paths
# -----------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

MODEL_DIR = BASE_DIR / "feedbackmodel" / "model_artifact"

MODEL_PATHS = {
    "severity": MODEL_DIR / "severity",
    "urgency": MODEL_DIR / "urgency",
    "impact": MODEL_DIR / "impact",
}


# -----------------------------
# Model Loading
# -----------------------------
def load_models() -> Dict[str, dict]:
    """
    Load vectorizer + model for all dimensions.

    Returns:
        {
            "severity": {"vectorizer": ..., "model": ...},
            "urgency":  {"vectorizer": ..., "model": ...},
            "impact":   {"vectorizer": ..., "model": ...},
        }
    """
    models = {}

    for dim, path in MODEL_PATHS.items():
        models[dim] = {
            "vectorizer": joblib.load(path / "vectorizer.joblib"),
            "model": joblib.load(path / "model.joblib"),
        }

    return models


# -----------------------------
# Prediction Helpers
# -----------------------------
def predict_dimension(vectorizer, model, text: str) -> dict:
    """
    Predict label + probabilities for a single dimension.
    """
    X = vectorizer.transform([text])

    label: Label = model.predict(X)[0]
    probs = model.predict_proba(X)[0]

    return {
        "label": label,
        "probs": dict(zip(model.classes_, probs)),
        "confidence": float(np.max(probs)),
    }


def predict_all_dimensions(models: Dict[str, dict], text: str) -> Dict[str, dict]:
    """
    Run prediction for severity, urgency, and impact.
    """
    return {
        dim: predict_dimension(
            models[dim]["vectorizer"],
            models[dim]["model"],
            text,
        )
        for dim in DIMENSIONS
    }


# -----------------------------
# Priority Logic (Business Layer)
# -----------------------------
def compute_priority_score(
    severity: Label,
    urgency: Label,
    impact: Label,
) -> float:
    """
    Weighted priority score.
    """
    return (
        0.45 * LABEL_TO_SCORE[urgency]
        + 0.35 * LABEL_TO_SCORE[severity]
        + 0.20 * LABEL_TO_SCORE[impact]
    )


def bucket_priority(score: float) -> PriorityLabel:
    """
    Convert numeric score into a priority label.
    """
    if score >= 2.5:
        return "critical"
    elif score >= 1.8:
        return "high"
    elif score >= 1.0:
        return "medium"
    else:
        return "low"


# -----------------------------
# Public API (what FastAPI calls)
# -----------------------------
def predict_with_priority(models: Dict[str, dict], text: str) -> dict:
    """
    Full prediction pipeline used by the backend API.
    """
    predictions = predict_all_dimensions(models, text)

    severity = predictions["severity"]["label"]
    urgency = predictions["urgency"]["label"]
    impact = predictions["impact"]["label"]

    score = compute_priority_score(severity, urgency, impact)

    return {
        "dimensions": predictions,
        "priority": {
            "label": bucket_priority(score),
            "score": round(score, 3),
        },
    }
