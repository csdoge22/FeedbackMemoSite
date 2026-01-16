# dataset/embedding/embed_text.py
import numpy as np
from sentence_transformers import SentenceTransformer
from dataset.processing.preprocessing import preprocess_text_series

MODEL_NAME = "all-MiniLM-L6-v2"

# Global cached model
_MODEL_CACHE: SentenceTransformer | None = None

def embed_text(text: str, model_name: str = MODEL_NAME) -> np.ndarray:
    """
    Converts a single string into a vector embedding using SentenceTransformer.
    Uses a cached model for efficiency.
    """
    global _MODEL_CACHE
    if _MODEL_CACHE is None:
        print(f"[INFO] Loading embedding model '{model_name}'...")
        _MODEL_CACHE = SentenceTransformer(model_name)

    preprocessed = preprocess_text_series([text])
    embedding = _MODEL_CACHE.encode(preprocessed, show_progress_bar=False)
    return embedding[0]  # returns a 1D numpy array
