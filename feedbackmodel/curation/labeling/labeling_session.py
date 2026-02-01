from typing import List
from curation.metadata.metadata import ActiveLearningMetadata
from curation.labeling.human_labeling import HumanLabeling

class LabelingSession:
    """
    Maintains state of a human-in-the-loop labeling session.
    """

    def __init__(self, metadata: ActiveLearningMetadata, human_labeling: HumanLabeling):
        self.metadata = metadata
        self.human_labeling = human_labeling
        self.current_batch: List[int] = []
        self.label_seed()

    def start_batch(self, indices: List[int]):
        """
        Set current batch for labeling.
        """
        self.current_batch = indices

    def label_current_batch(self, model_id: str):
        """
        Label the current batch using human labeling + RAG + LLM.
        """
        if not self.current_batch:
            return
        self.human_labeling.label_batch(self.current_batch, model_id)
        self.current_batch = []

    def label_seed(self):
        seed_indices = []
        seed_proposals = []

        for r in self.metadata.records:
            proposal = r.get("seed_proposal")
            if proposal is not None:
                seed_indices.append(r["index"])
                seed_proposals.append(proposal)

        if seed_indices:
            self.metadata.mark_as_labeled(seed_indices, seed_proposals)