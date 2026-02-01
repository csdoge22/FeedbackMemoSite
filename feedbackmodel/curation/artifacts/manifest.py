# curation/artifacts/manifest.py

from pathlib import Path
from typing import List
import json
import time


def write_manifest(
    *,
    artifact_root: Path,
    dimensions: List[str],
    artifact_version: str = "1.0",
) -> None:
    manifest = {
        "created_at": time.time(),
        "artifact_version": artifact_version,
        "dimensions": dimensions,
        "pipeline_type": "independent_per_dimension_classifiers",
    }

    with open(artifact_root / "artifact_manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)


def load_manifest(artifact_root: Path) -> dict:
    path = artifact_root / "artifact_manifest.json"

    if not path.exists():
        raise FileNotFoundError("Missing artifact_manifest.json")

    with open(path, encoding="utf-8") as f:
        return json.load(f)
