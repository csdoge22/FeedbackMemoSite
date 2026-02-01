from curation.labeling.labeling_session import LabelingSession
from curation.metadata.metadata import ActiveLearningMetadata
from curation.seeds.seed_factory import default_seed_proposal


class DummyHumanLabeling:
    def __init__(self):
        self.called = False

    def label_batch(self, indices, model_id):
        self.called = True


def test_labeling_session_calls_human_labeling():
    metadata = ActiveLearningMetadata(
        feedback_texts=["Feedback"],
        seed_indices=[0],
        seed_proposal_factory=default_seed_proposal,
    )

    human = DummyHumanLabeling()
    session = LabelingSession(metadata, human)

    session.start_batch([0])
    session.label_current_batch("model-x")

    assert human.called
    assert session.current_batch == []
