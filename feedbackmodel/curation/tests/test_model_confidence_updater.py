import pytest
from curation.metadata.metadata import ActiveLearningMetadata
from curation.model.model_confidence_updater import ModelConfidenceUpdater

# -------------------------------------------------------------------
# Dummy seed proposal for testing
# -------------------------------------------------------------------

def dummy_seed_proposal(idx, text):
    if idx == 0:
        return {
            "severity": "high",
            "urgency": "medium",
            "impact": "low"
        }
    else:
        return {
            "severity": "low",
            "urgency": "high",
            "impact": "medium"
        }

# -------------------------------------------------------------------
# Fixtures
# -------------------------------------------------------------------

@pytest.fixture
def metadata():
    feedbacks = [
        "Server crashed after update",
        "UI button misaligned",
        "API response slow",
    ]

    # TWO labeled seeds with different classes
    seed_indices = [0, 1]

    metadata = ActiveLearningMetadata(
        feedback_texts=feedbacks,
        seed_indices=seed_indices,
        seed_proposal_factory=dummy_seed_proposal
    )

    metadata.apply_labels(
        0,
        labels={"severity": "high", "urgency": "medium", "impact": "low"},
        confidences={"severity": 1.0, "urgency": 1.0, "impact": 1.0},
    )

    metadata.apply_labels(
        1,
        labels={"severity": "low", "urgency": "high", "impact": "medium"},
        confidences={"severity": 1.0, "urgency": 1.0, "impact": 1.0},
    )

    return metadata

# -------------------------------------------------------------------
# Tests
# -------------------------------------------------------------------

def test_model_confidence_updater_fit_and_predict(metadata):
    model = ModelConfidenceUpdater()

    model.fit(metadata)

    # Now this is statistically valid
    assert any(model.is_fitted.values())

    model.update_unlabeled_confidences(metadata)

    for record in metadata.records:
        if not record["labeled"]:
            assert "confidences" in record
            assert record["confidence_source"] == "multinomial_nb"
