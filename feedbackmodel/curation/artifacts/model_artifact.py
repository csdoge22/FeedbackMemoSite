# curation/artifacts/model_artifact.py

from dataclasses import dataclass, asdict
from typing import Dict, Any, List
from pathlib import Path
import json
import joblib
import time
import sklearn


@dataclass
class ModelArtifact:
    """
    Wrapper for a trained classifier + vectorizer + labels + metadata.
    Designed for inference-only saving and reproducible reloads.
    """
    model: Any
    vectorizer: Any
    labels: List[str]
    metadata: Dict[str, Any]

    def __post_init__(self):
        # Automatically augment metadata with reproducibility info
        self.metadata.setdefault("sklearn_version", sklearn.__version__)
        self.metadata.setdefault("vectorizer_type", type(self.vectorizer).__name__)
        self.metadata.setdefault("model_type", type(self.model).__name__)
        self.metadata.setdefault("created_at", time.time())

    def save(self, path: Path):
        """
        Save model, vectorizer, and metadata to the given path.
        """
        path.mkdir(parents=True, exist_ok=True)

        # Save model + vectorizer
        joblib.dump(self.model, path / "model.joblib")
        joblib.dump(self.vectorizer, path / "vectorizer.joblib")

        # Save metadata
        with open(path / "metadata.json", "w") as f:
            json.dump(self.metadata, f, indent=2)

    @classmethod
    def load(cls, path: Path) -> "ModelArtifact":
        """
        Reload an artifact from disk.
        """
        model = joblib.load(path / "model.joblib")
        vectorizer = joblib.load(path / "vectorizer.joblib")

        with open(path / "metadata.json") as f:
            metadata = json.load(f)

        labels = metadata.get("labels", [])

        return cls(
            model=model,
            vectorizer=vectorizer,
            labels=labels,
            metadata=metadata,
        )
