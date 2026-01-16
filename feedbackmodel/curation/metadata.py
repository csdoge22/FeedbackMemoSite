from typing import List, Dict, Optional
from .dimension_label_proposal import DimensionLabelProposal

class ActiveLearningMetadata:
    """
    Stores labeled feedback and derived priorities.
    Supports pre-labeled seed items for active learning.
    """

    def __init__(
        self,
        feedback_texts: List[str],
        seed_indices: Optional[List[int]] = None,
        seed_proposal_factory=None
    ):
        self.records: List[Dict] = []

        for i, text in enumerate(feedback_texts):
            record = {
                "text": text,
                "labels": {},
                "priority": None,
                "labeled": False,
                "cluster_label": None,
                "seed_proposal": None,  # store initial seed proposal if any
            }

            # If this index is a seed, generate its proposal
            if seed_indices and seed_proposal_factory and i in seed_indices:
                proposal = seed_proposal_factory(i, text)
                record["labels"] = {dim: lv.value for dim, lv in proposal.labels.items()}
                record["priority"] = 1.0  # seeds can start with high priority
                record["labeled"] = True
                record["seed_proposal"] = proposal

            self.records.append(record)

    def add_feedback(self, feedback_text: str, labels: Optional[Dict[str, str]] = None):
        """Add a new unlabeled feedback item."""
        record = {
            "text": feedback_text,
            "labels": labels or {},
            "priority": None,
            "labeled": False,
            "cluster_label": None,
            "seed_proposal": None,
        }
        self.records.append(record)

    def mark_as_labeled(self, indices: List[int], proposals: List[DimensionLabelProposal]):
        """
        Mark feedback items as labeled using DimensionLabelProposal.
        Updates labels, priority, and marks them as labeled.
        """
        for idx, proposal in zip(indices, proposals):
            self.records[idx]["labels"] = {dim: lv.value for dim, lv in proposal.labels.items()}
            from .priority_utils import compute_priority
            self.records[idx]["priority"] = compute_priority(self.records[idx]["labels"])
            self.records[idx]["labeled"] = True
            # Update seed_proposal if this was initially a seed
            if self.records[idx]["seed_proposal"] is None:
                self.records[idx]["seed_proposal"] = proposal

    def done(self) -> bool:
        """Return True if all feedback items have been labeled."""
        return all(r["labeled"] for r in self.records)

    def save(self, path="metadata.json"):
        """Save metadata to JSON."""
        import json
        serializable_records = []
        for r in self.records:
            rec = r.copy()
            # Convert seed_proposal to dict if present
            if rec.get("seed_proposal"):
                rec["seed_proposal"] = {
                    "labels": {k: v.value for k, v in rec["seed_proposal"].labels.items()},
                    "confidences": rec["seed_proposal"].confidences,
                    "rationale": rec["seed_proposal"].rationale,
                    "source": rec["seed_proposal"].source,
                    "model_id": rec["seed_proposal"].model_id,
                    "evidence": [
                        {
                            "text": e.text,
                            "labels": e.labels,
                            "priority": e.priority,
                            "metadata": e.metadata,
                            "distance": getattr(e, "distance", None)
                        } for e in rec["seed_proposal"].evidence
                    ]
                }
            serializable_records.append(rec)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(serializable_records, f, indent=2)
        print(f"[Saved] Metadata saved to {path}")
