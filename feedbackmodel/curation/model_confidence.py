from typing import List
import numpy as np

from sklearn.naive_bayes import MultinomialNB
from sklearn.feature_extraction.text import TfidfVectorizer

from .metadata import ActiveLearningMetadata


class ModelConfidenceUpdater:
    """
    Trains a classifier on labeled data and updates confidence
    scores on the unlabeled pool.
    """

    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            ngram_range=(1, 2),
            stop_words="english",
        )
        self.model = MultinomialNB()
        self.is_fitted = False

    def fit(self, metadata: ActiveLearningMetadata):
        texts = []
        labels = []

        for r in metadata.records:
            if not r["labeled"]:
                continue

            # Example: single-task classification
            # (adjust if you go multi-dim later)
            label = r["labels"].get("severity")
            if label is None:
                continue

            texts.append(r["text"])
            labels.append(label)

        if len(set(labels)) < 2:
            return  # not enough signal yet

        X = self.vectorizer.fit_transform(texts)
        self.model.fit(X, labels)
        self.is_fitted = True

    def update_unlabeled_confidences(self, metadata: ActiveLearningMetadata):
        if not self.is_fitted:
            return

        unlabeled_indices = [
            i for i, r in enumerate(metadata.records)
            if not r["labeled"]
        ]

        if not unlabeled_indices:
            return

        texts = [metadata.records[i]["text"] for i in unlabeled_indices]
        X = self.vectorizer.transform(texts)

        probs = self.model.predict_proba(X)

        for idx, p in zip(unlabeled_indices, probs):
            metadata.records[idx]["confidences"]["model"] = float(np.max(p))
            metadata.records[idx]["confidence_source"] = "multinomial_nb"
