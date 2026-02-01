import json
from unittest.mock import patch
import pytest

from curation.labeling.human_labeling import HumanLabeling
from curation.metadata.metadata import ActiveLearningMetadata
from curation.seeds.seed_factory import default_seed_proposal
from curation.dimension_label_proposal import LabelValue

# -------------------------------------------------------------------
# Dummy classes/functions for testing
# -------------------------------------------------------------------

class DummyRAGClient:
    def retrieve_similar(self, embedding):
        return []

def dummy_llm(prompt):
    return json.dumps({
        "labels": {"severity": "high"},
        "confidences": {"severity": 0.9},
        "evidence": [],
        "source": "llm",
        "model_id": "test-model"
    })

def make_metadata():
    return ActiveLearningMetadata(
        feedback_texts=["Feedback 1"],
        seed_indices=[0],
        seed_proposal_factory=default_seed_proposal,
    )

# -------------------------------------------------------------------
# Tests
# -------------------------------------------------------------------

@patch("curation.labeling.human_labeling.encode_texts")
def test_human_labeling_labels_batch(mock_encode):
    mock_encode.return_value = [[0.0, 0.0, 0.0]]

    metadata = make_metadata()
    labeling = HumanLabeling(metadata, DummyRAGClient(), dummy_llm)

    labeling.label_batch([0], model_id="test-model")

    record = metadata.get_record(0)
    assert record["labeled"] is True

    # Use helper to check plain string labels
    labels_dict = metadata.get_labels_as_dict(0)
    assert labels_dict["severity"] == "high"

@pytest.mark.parametrize("indices", [[0]])
def test_metadata_mark_as_labeled(indices):
    metadata = make_metadata()
    from curation.dimension_label_proposal import DimensionLabelProposal

    proposal = DimensionLabelProposal(
        labels={"severity": LabelValue("high")},
        confidences={"severity": 0.9},
        rationale={},
        evidence=[],
        source="test",
        model_id="test-model"
    )

    metadata.mark_as_labeled(indices, [proposal])

    record = metadata.get_record(0)
    assert record["labeled"] is True
    # Plain strings assertion
    labels_dict = metadata.get_labels_as_dict(0)
    assert labels_dict["severity"] == "high"
