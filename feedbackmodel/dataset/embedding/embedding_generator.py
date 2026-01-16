import os
import numpy as np
from sentence_transformers import SentenceTransformer
from dataset.processing.dataset_loader import load_dataset, get_split_ids
from dataset.processing.preprocessing import preprocess_text_series

MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIR = os.path.join(os.path.dirname(__file__), "../data/embeddings")
os.makedirs(EMBEDDING_DIR, exist_ok=True)

_MODEL_CACHE: SentenceTransformer | None = None


def encode_texts(texts: list[str], model_name: str = MODEL_NAME) -> np.ndarray:
    """Generate float32 embeddings for a list of texts."""
    global _MODEL_CACHE
    if _MODEL_CACHE is None:
        print(f"[INFO] Loading embedding model '{model_name}'...")
        _MODEL_CACHE = SentenceTransformer(model_name)

    texts = preprocess_text_series(texts)
    embeddings = _MODEL_CACHE.encode(texts, show_progress_bar=True)
    return np.asarray(embeddings, dtype=np.float32)


def encode_dataset_split(split_name: str) -> tuple[list[str], np.ndarray]:
    df = load_dataset(split_name)
    if "feedback_text" not in df.columns:
        raise ValueError("Dataset must contain 'feedback_text' column.")

    ids = get_split_ids(split_name)
    cache_path = os.path.join(
        EMBEDDING_DIR, f"{split_name}_{MODEL_NAME}_{df.shape[0]}rows.npy"
    )

    if os.path.exists(cache_path):
        embeddings = np.load(cache_path)
        print(f"Loaded cached embeddings for '{split_name}' ({df.shape[0]} rows).")
    else:
        embeddings = encode_texts(df["feedback_text"].tolist())
        np.save(cache_path, embeddings)

    return ids, embeddings
