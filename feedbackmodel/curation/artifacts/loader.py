# curation/artifacts/loader.py

from pathlib import Path
from typing import Dict

from .model_artifact import ModelArtifact


def load_all_artifacts(artifact_root: Path) -> Dict[str, ModelArtifact]:
    """
    Load all dimension artifacts into memory for inference.
    """

    artifacts = {}

    for dimension_dir in artifact_root.iterdir():
        if not dimension_dir.is_dir():
            continue

        artifact = ModelArtifact.load(dimension_dir)
        dimension = artifact.metadata["dimension"]

        artifacts[dimension] = artifact

    return artifacts
