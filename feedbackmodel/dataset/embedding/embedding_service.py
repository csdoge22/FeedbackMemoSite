# dataset/embedding/embedding_service.py
import os
import numpy as np
from typing import List
from sentence_transformers import SentenceTransformer
from dataset.processing.preprocessing import preprocess_text_series

MODEL_NAME = "all-MiniLM-L6-v2"

class EmbeddingService:
    """
    Service to convert text to embeddings using SentenceTransformer.
    Uses internal caching for efficiency.
    """

    def __init__(self, model_name: str = MODEL_NAME):
        self.model_name = model_name
        self._model: SentenceTransformer | None = None

    def _load_model(self):
        if self._model is None:
            print(f"[INFO] Loading embedding model '{self.model_name}'...")
            self._model = SentenceTransformer(self.model_name)

    def embed_text(self, text: str) -> np.ndarray:
        """
        Convert a single string into a 1D embedding vector.
        """
        self._load_model()
        preprocessed = preprocess_text_series([text])
        embedding = self._model.encode(preprocessed, show_progress_bar=False)
        return embedding[0]

    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """
        Convert a list of strings into embeddings.
        Returns a 2D numpy array of shape (len(texts), embedding_dim).
        """
        self._load_model()
        preprocessed = preprocess_text_series(texts)
        embeddings = self._model.encode(preprocessed, show_progress_bar=True)
        return np.asarray(embeddings, dtype=np.float32)
