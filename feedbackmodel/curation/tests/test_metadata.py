import pytest
from curation.metadata.metadata import ActiveLearningMetadata
from curation.seeds.seed_factory import default_seed_proposal

def make_metadata():
    return ActiveLearningMetadata(
        feedback_texts=["Feedback A"],
        seed_indices=[0],
        seed_proposal_factory=default_seed_proposal,
    )

def test_metadata_initializes_records():
    metadata = make_metadata()
    # Ensure the seed record exists
    record = metadata.records[0]
    assert "text" in record
    assert record["text"] == "Feedback A"
    assert "labels" in record
    assert isinstance(record["labels"], dict)

def test_mark_as_labeled_adds_proposal():
    metadata = make_metadata()
    # Create a dummy proposal for marking
    proposal = metadata.records[0]["seed_proposal"]
    metadata.mark_as_labeled([0], [proposal])

    # Check that the record is marked labeled
    assert metadata.records[0]["labeled"] is True
    assert metadata.records[0]["labels"] == proposal.labels
