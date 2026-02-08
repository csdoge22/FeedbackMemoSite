import json
import numpy as np
from pathlib import Path
from typing import List, Tuple
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import logging

from dataset.processing.load_splits import load_split
from curation.utils.rag_client import CollectionClient

logger = logging.getLogger(__name__)

CACHE_DIR = Path(__file__).parent.parent / "data" / "embeddings"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

MODEL_DIR = Path(__file__).parent.parent / "embedding" / "all-MiniLM-L6-v2"

class EmbeddingCacheClient(CollectionClient):
    def __init__(self, split: str = "train", top_k: int = 5):
        # 1. Force offline mode at the application level
        import os
        os.environ["TRANSFORMERS_OFFLINE"] = "1"
        os.environ["HF_HUB_OFFLINE"] = "1"

        self.split = split
        self.top_k = top_k
        self._cache_path = CACHE_DIR / f"{split}_embeddings.npy"
        self._texts_path = CACHE_DIR / f"{split}_texts.json"
        
        # Ensure the directory exists before loading
        if not MODEL_DIR.exists():
            raise FileNotFoundError(f"Model directory not found at {MODEL_DIR}. "
                                    "Ensure you've downloaded the model files manually.")

        # Load purely from the local path
        self._model = SentenceTransformer(
            str(MODEL_DIR), 
            device="cpu", # Explicitly setting device can prevent unnecessary CUDA checks
            local_files_only=True
        )
        self._loaded = False
        self._load_or_compute()

    def _load_or_compute(self):
        if self._cache_path.exists() and self._texts_path.exists():
            self._embeddings = np.load(self._cache_path)
            self._texts = json.load(open(self._texts_path))
            logger.info(f"[EmbeddingCache] Loaded '{self.split}'")
        else:
            df = load_split(self.split)
            self._texts = df["feedback_text"].tolist()
            self._embeddings = self._model.encode(
                self._texts, convert_to_numpy=True, show_progress_bar=True
            )
            np.save(self._cache_path, self._embeddings)
            json.dump(self._texts, open(self._texts_path, "w"))
            logger.info(f"[EmbeddingCache] Computed '{self.split}'")
        self._loaded = True

    def encode_texts(self, texts: List[str]) -> np.ndarray:
        return self._model.encode(texts, convert_to_numpy=True)

    def retrieve(self, query_embedding: List[float], top_k: int = None):
        top_k = top_k or self.top_k
        sims = cosine_similarity(
            np.array(query_embedding).reshape(1, -1),
            self._embeddings
        ).flatten()
        idx = sims.argsort()[::-1][:top_k]
        return [(self._texts[i], {}, {}, float(1 - sims[i])) for i in idx]
