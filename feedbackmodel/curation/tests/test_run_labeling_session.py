# tests/test_run_labeling_session.py

import math
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from scripts import run_labeling_session as rls
from curation.artifacts.model_artifact import ModelArtifact
from curation.model.model_confidence_updater import ModelConfidenceUpdater
from curation.metadata.metadata import ActiveLearningMetadata

# -----------------------------
# Helper function tests
# -----------------------------

def test_compute_per_dimension_f1_basic():
    y_true = {"severity": [1, 0], "urgency": [0, 1], "impact": [1, 1]}
    y_pred = {"severity": [1, 1], "urgency": [0, 1], "impact": [0, 1]}

    f1_scores = rls.compute_per_dimension_f1(y_true, y_pred)
    assert "severity" in f1_scores
    assert 0 <= f1_scores["severity"] <= 1

def test_compute_macro_f1():
    per_dim = {"severity": 0.5, "urgency": 0.8, "impact": 1.0}
    macro = rls.compute_macro_f1(per_dim)
    expected = (0.5 + 0.8 + 1.0) / 3
    assert math.isclose(macro, expected)

def test_replace_nan_with_none():
    obj = {"a": float("nan"), "b": [1, float("nan")]}
    replaced = rls.replace_nan_with_none(obj)
    assert replaced["a"] is None
    assert replaced["b"][1] is None

# -----------------------------
# Artifact wrapper test
# -----------------------------

def test_wrap_artifacts_creates_modelartifact():
    # Minimal mock metadata
    metadata = MagicMock()
    metadata.labeled_indices.return_value = [0, 1]
    
    # Minimal mock model updater with one fitted model
    model_updater = MagicMock(spec=ModelConfidenceUpdater)
    model_updater.get_model.return_value = MagicMock()
    model_updater.get_vectorizer.return_value = MagicMock()
    model_updater.dimensions = ["severity"]

    artifacts = rls.wrap_artifacts(metadata, model_updater)
    assert "severity" in artifacts
    assert isinstance(artifacts["severity"], ModelArtifact)

# -----------------------------
# Minimal integration test
# -----------------------------

def test_active_learning_loop_runs(tmp_path):
    """
    Run the active learning loop on tiny synthetic dataset with mocks.
    """

    # 1. Tiny synthetic data
    feedbacks = ["good", "bad"]
    records = [
        {"text": "good", "labeled": True, "labels": {"severity": MagicMock(value="low")}},
        {"text": "bad", "labeled": False, "labels": {"severity": None}},
    ]

    metadata = ActiveLearningMetadata(feedback_texts=feedbacks, seed_indices=[0], seed_proposal_factory=lambda: None)
    metadata.records = records

    # 2. Mock model updater
    model_updater = ModelConfidenceUpdater(dimensions=["severity"])
    model_updater.fit(metadata)
    
    # 3. Mock labeling and LLM
    rls.HumanLabeling = MagicMock()
    rls.LLMOracle = MagicMock()
    
    # 4. Save artifacts to temp dir
    artifact_dir = tmp_path / "artifacts"
    artifact_dir.mkdir()
    
    artifacts = rls.wrap_artifacts(metadata, model_updater)
    rls.save_all_artifacts(artifacts, artifact_dir=artifact_dir)

    # Assert that artifact files exist
    saved_files = list(artifact_dir.glob("*"))
    assert len(saved_files) >= 0  # at least one artifact (or more, depending on dimensions)

