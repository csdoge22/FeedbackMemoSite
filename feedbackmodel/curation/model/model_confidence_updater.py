import logging
from typing import List, Dict
import numpy as np
from sklearn.naive_bayes import MultinomialNB
from sklearn.feature_extraction.text import TfidfVectorizer

from curation.metadata.metadata import ActiveLearningMetadata
from curation.model.base_model import BaseModel

logger = logging.getLogger(__name__)

class ModelConfidenceUpdater(BaseModel):
    """
    Multi-label ML model for updating confidences in Active Learning.
    Uses separate MultinomialNB + TF-IDF models for each dimension.
    """

    def __init__(self, dimensions: List[str] = None):
        self.dimensions = dimensions or ["severity", "urgency", "impact"]
        self.vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1, 2), stop_words="english")
        # One MultinomialNB model per dimension
        self.models: Dict[str, MultinomialNB] = {dim: MultinomialNB() for dim in self.dimensions}
        self.is_fitted: Dict[str, bool] = {dim: False for dim in self.dimensions}

    def fit(self, metadata: ActiveLearningMetadata):
        """
        Fit a separate MultinomialNB model for each dimension on all labeled examples.
        Handles missing labels per dimension and ensures X/y lengths match.
        """
        labeled_records = [r for r in metadata.records if r["labeled"]]

        if not labeled_records:
            logger.info("No labeled examples to fit models")
            return

        for dim in self.dimensions:
            # Only include records that have a label for this dimension
            dim_records = [r for r in labeled_records if dim in r["labels"] and r["labels"][dim] is not None]

            if not dim_records:
                logger.info(f"No labels found for dimension '{dim}'")
                continue

            texts_dim = [r["text"] for r in dim_records]
            X_dim = self.vectorizer.fit_transform(texts_dim)  # refit TF-IDF every iteration

            values = [r["labels"][dim].value for r in dim_records]

            # Must have at least 2 unique values to fit a classifier
            if len(set(values)) < 2:
                logger.info(f"Not enough label diversity to fit model for '{dim}'")
                continue

            self.models[dim].fit(X_dim, values)
            self.is_fitted[dim] = True
            logger.info(f"Fitted model for dimension '{dim}' on {len(values)} examples")

    def update_unlabeled_confidences(self, metadata: ActiveLearningMetadata):
        """
        Update per-dimension confidences for all unlabeled examples.
        """

        if not any(self.is_fitted.values()):
            logger.info("No fitted models available; skipping confidence update")
            return

        unlabeled_indices = [i for i, r in enumerate(metadata.records) if not r["labeled"]]
        if not unlabeled_indices:
            logger.info("No unlabeled examples to update")
            return

        texts = [metadata.records[i]["text"] for i in unlabeled_indices]
        X = self.vectorizer.transform(texts)

        for dim in self.dimensions:
            if not self.is_fitted[dim]:
                continue
            probs = self.models[dim].predict_proba(X)
            for idx, p in zip(unlabeled_indices, probs):
                if "confidences" not in metadata.records[idx]:
                    metadata.records[idx]["confidences"] = {}
                metadata.records[idx]["confidences"][dim] = float(np.max(p))
                metadata.records[idx]["confidence_source"] = "multinomial_nb"

    # --- Implement BaseModel interface ---
    def predict(self, texts: List[str]) -> Dict[str, List[str]]:
        """
        Predict labels for all dimensions.
        Returns a dict: {dimension -> list of predictions}.
        """
        if not texts:
            return {dim: [] for dim in self.dimensions}

        X = self.vectorizer.transform(texts)
        predictions = {}
        for dim in self.dimensions:
            if self.is_fitted[dim]:
                preds = self.models[dim].predict(X)
                predictions[dim] = preds.tolist()
            else:
                predictions[dim] = [None] * len(texts)
        return predictions

    # -----------------------------
    # NEW ACCESSOR METHODS
    # -----------------------------
    def get_model(self, dim: str) -> MultinomialNB:
        """
        Return the classifier for a given dimension.
        Raises KeyError if dimension is invalid or model is not fitted.
        """
        if dim not in self.models:
            raise KeyError(f"Dimension '{dim}' not found in models")
        if not self.is_fitted[dim]:
            raise ValueError(f"Model for dimension '{dim}' is not fitted yet")
        return self.models[dim]

    def get_vectorizer(self) -> TfidfVectorizer:
        """
        Return the shared TF-IDF vectorizer.
        """
        return self.vectorizer
