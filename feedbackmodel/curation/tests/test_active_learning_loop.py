import pytest
from unittest.mock import MagicMock
from pathlib import Path

from curation.metadata.metadata import ActiveLearningMetadata
from curation.model.model_confidence_updater import ModelConfidenceUpdater
from curation.labeling.human_labeling import HumanLabeling
from curation.query.query_strategies import least_confidence_sampling
from curation.artifacts.model_artifact import ModelArtifact
from curation.artifacts.saver import save_all_artifacts

# -------------------------------
# Mock LLM and Stopping
# -------------------------------
class MockLLMOracle:
    def label(self, prompt):
        return "low"

class MockStopper:
    def __init__(self):
        self.called = 0

    def update(self, stop_snapshot):
        self.called += 1
        # Always return True to simulate stopping after first iteration
        return True

class MockMetricsTracker:
    def log(self, payload):
        pass


@pytest.fixture
def tiny_metadata():
    # Ensure diversity for MultinomialNB
    records = [
        {"text": "good feedback",   "labeled": True,  "labels": {"severity": MagicMock(value="low")}},
        {"text": "bad feedback",    "labeled": True,  "labels": {"severity": MagicMock(value="high")}},
        {"text": "neutral feedback","labeled": False, "labels": {"severity": None}},
    ]
    metadata = ActiveLearningMetadata(
        feedback_texts=[r["text"] for r in records],
        seed_indices=[0, 1],  # Seeds with diverse labels
        seed_proposal_factory=lambda idx, text: records[idx]["labels"]["severity"]
    )

    # Override records for simplicity
    metadata.records = records
    return metadata


@pytest.fixture
def model_updater():
    return ModelConfidenceUpdater(dimensions=["severity"])


def test_active_learning_loop_real_model(tmp_path, tiny_metadata, model_updater):
    metadata = tiny_metadata
    llm_oracle = MockLLMOracle()
    labeling = HumanLabeling(metadata, rag_client=MagicMock(), llm_call_fn=llm_oracle.label)

    # Stopper mock will not stabilize early
    class MockStopper:
        def __init__(self):
            self.called = 0
        def update(self, stop_snapshot):
            self.called += 1
            return False  # never halt early

    stopper = MockStopper()
    
    # Metrics mock
    class MockMetricsTracker:
        def __init__(self):
            self.logs = []
        def log(self, payload):
            self.logs.append(payload)

    metrics = MockMetricsTracker()

    stop_texts = [r["text"] for r in metadata.records]
    test_texts = [r["text"] for r in metadata.records]

    iteration = 0
    while not all(r["labeled"] for r in metadata.records):
        iteration += 1

        # Fit real models and update confidences
        model_updater.fit(metadata)
        model_updater.update_unlabeled_confidences(metadata)

        # Stopper decides whether to halt
        stop_snapshot = {i: {"severity": "low"} for i in range(len(stop_texts))}
        stabilized = stopper.update(stop_snapshot)

        # TEST F1 calculation
        true_snapshot = {"severity": [r["labels"]["severity"].value if r["labeled"] else "__unknown__"
                                      for r in metadata.records]}
        test_preds = model_updater.predict(test_texts)
        test_snapshot = {"severity": [pred or "__unknown__" for pred in test_preds["severity"]]}

        from sklearn.metrics import f1_score
        per_dim_f1 = {dim: f1_score(true_snapshot[dim], test_snapshot[dim], average="macro", zero_division=0)
                      for dim in ["severity"]}
        macro_f1 = sum(per_dim_f1.values()) / len(per_dim_f1)

        metrics.log({
            "iteration": iteration,
            "num_labeled": len([r for r in metadata.records if r["labeled"]]),
            "num_unlabeled": len([r for r in metadata.records if not r["labeled"]]),
            "stabilized": stabilized,
            "per_dimension_f1": per_dim_f1,
            "macro_f1": macro_f1,
        })

        # Pick least-confidence sample
        indices = least_confidence_sampling(metadata.records, n=1)
        # Fallback to first unlabeled if LC sampling fails
        if not indices:
            indices = [i for i, r in enumerate(metadata.records) if not r["labeled"]]

        # Label all selected indices
        for idx in indices:
            metadata.records[idx]["labeled"] = True
            metadata.records[idx]["labels"]["severity"] = MagicMock(value="low")

        # Wrap and save artifacts
        artifacts = {}
        for dim in ["severity"]:
            model = model_updater.models[dim]
            vectorizer = model_updater.vectorizer
            labels = model.classes_.tolist() if model_updater.is_fitted[dim] else []
            meta = {"dimension": dim, "num_training_examples": len([r for r in metadata.records if r["labeled"]]),
                    "created_at": 123}
            artifacts[dim] = ModelArtifact(model, vectorizer, labels, meta)

        artifact_dir = tmp_path / "artifacts"
        artifact_dir.mkdir(exist_ok=True)
        save_all_artifacts(artifacts, artifact_dir=artifact_dir)

    # -----------------------------
    # Assertions
    # -----------------------------
    assert stopper.called >= 1
    assert all(r["labeled"] for r in metadata.records)