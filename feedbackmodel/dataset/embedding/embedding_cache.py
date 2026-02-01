# dataset/embedding/embedding_cache.py

import os
import json
import numpy as np
from typing import List, Dict, Tuple
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer

CACHE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "embeddings"))
os.makedirs(CACHE_DIR, exist_ok=True)


class EmbeddingCache:
    """
    Manages embeddings for feedback texts, supports caching to disk.
    Integrates with SentenceTransformer 'all-MiniLM-L6-v2' to compute embeddings.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self._cache: Dict[str, np.ndarray] = {}        # split -> embeddings
        self._texts_cache: Dict[str, List[str]] = {}   # split -> texts
        self._loaded_splits: set[str] = set()
        self.model = SentenceTransformer(model_name)

    # -----------------------------
    # File helpers
    # -----------------------------
    def _get_cache_path_for_split(self, split: str) -> str:
        return os.path.join(CACHE_DIR, f"{split}_embeddings.npy")

    def _get_texts_path_for_split(self, split: str) -> str:
        return os.path.join(CACHE_DIR, f"{split}_texts.json")

    # -----------------------------
    # Load/save split cache
    # -----------------------------
    def load_split_cache(self, split: str) -> bool:
        """
        Load embeddings and texts from disk for a split.
        Returns True if successful, False otherwise.
        """
        path = self._get_cache_path_for_split(split)
        texts_path = self._get_texts_path_for_split(split)
        if os.path.exists(path) and os.path.exists(texts_path):
            self._cache[split] = np.load(path)
            with open(texts_path, "r", encoding="utf-8") as f:
                self._texts_cache[split] = json.load(f)
            self._loaded_splits.add(split)
            return True
        return False

    def save_split_cache(self, split: str):
        """
        Save a split's embeddings and texts to disk.
        """
        if split not in self._cache or split not in self._texts_cache:
            return
        np.save(self._get_cache_path_for_split(split), self._cache[split])
        with open(self._get_texts_path_for_split(split), "w", encoding="utf-8") as f:
            json.dump(self._texts_cache[split], f)

    # -----------------------------
    # Set embeddings directly
    # -----------------------------
    def set_split_embeddings(self, split: str, texts: List[str], embeddings: np.ndarray):
        """
        Set embeddings and texts directly for a split.
        Automatically saves to disk.
        """
        if len(texts) != embeddings.shape[0]:
            raise ValueError("Number of texts must match number of embeddings")
        self._cache[split] = embeddings.astype(np.float32)
        self._texts_cache[split] = texts
        self._loaded_splits.add(split)
        self.save_split_cache(split)

    # -----------------------------
    # Compute embeddings
    # -----------------------------
    def get_embeddings_for_texts(self, texts: List[str]) -> np.ndarray:
        """
        Compute embeddings for arbitrary texts using SentenceTransformer.
        """
        embeddings = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
        return embeddings.astype(np.float32)

    def get_embeddings_for_split(self, split: str) -> np.ndarray:
        """
        Return embeddings for a split, loading from disk if available,
        or compute on-the-fly if texts are provided externally.
        """
        if split in self._cache:
            return self._cache[split]
        if self.load_split_cache(split):
            return self._cache[split]
        raise ValueError(f"Split '{split}' not available in cache. Use set_split_embeddings first.")

    # -----------------------------
    # Retrieve top-k similar texts for RAG
    # -----------------------------
    def retrieve_similar(
        self,
        query_embedding: np.ndarray,
        split: str,
        top_k: int = 5
    ) -> Tuple[List[str], List[float]]:
        """
        Returns top-k most similar texts and distances from a split's embeddings.
        """
        if split not in self._cache:
            raise ValueError(f"Split '{split}' not loaded in EmbeddingCache")

        embeddings = self._cache[split]
        texts = self._texts_cache[split]

        sims = cosine_similarity(query_embedding.reshape(1, -1), embeddings).flatten()
        top_indices = np.argsort(sims)[::-1][:top_k]

        top_texts = [texts[i] for i in top_indices]
        top_distances = [1.0 - sims[i] for i in top_indices]  # distance = 1 - similarity

        return top_texts, top_distances

    # -----------------------------
    # Save all loaded splits
    # -----------------------------
    def save_all(self):
        for split in self._loaded_splits:
            self.save_split_cache(split)
