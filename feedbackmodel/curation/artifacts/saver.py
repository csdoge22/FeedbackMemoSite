# curation/artifacts/saver.py

from pathlib import Path
import json
import time
from typing import Dict
from curation.artifacts.model_artifact import ModelArtifact

MANIFEST_FILENAME = "artifact_manifest.json"

def save_all_artifacts(
    artifacts: Dict[str, ModelArtifact],
    artifact_dir: Path,
    artifact_version: str = "1.0",
    pipeline_type: str = "independent_per_dimension_classifiers",
):
    """
    Save all ModelArtifacts to disk under artifact_dir.
    Each dimension gets its own subfolder (overwrites by default).

    Also writes a global manifest for deployment and reproducibility.
    """

    artifact_dir.mkdir(parents=True, exist_ok=True)

    # Save each artifact
    for dim, artifact in artifacts.items():
        # Ensure labels are in metadata for reproducibility
        artifact.metadata["labels"] = artifact.labels

        # Path for this dimension
        dim_path = artifact_dir / dim
        artifact.save(dim_path)

    # Write global manifest
    manifest = {
        "created_at": int(time.time()),
        "dimensions": list(artifacts.keys()),
        "artifact_version": artifact_version,
        "pipeline_type": pipeline_type,
    }

    manifest_path = artifact_dir / MANIFEST_FILENAME
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
