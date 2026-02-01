# curation/metadata.py

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Any

from curation.dimension_label_proposal import LabelValue, DimensionLabelProposal

# ---------------------------------------------------------------------
# Prediction History
# ---------------------------------------------------------------------

@dataclass
class PredictionHistory:
    snapshots: List[Dict[int, Dict[str, str]]] = field(default_factory=list)

    def add_snapshot(self, predictions: Dict[int, Dict[str, str]]) -> None:
        self.snapshots.append({k: dict(v) for k, v in predictions.items()})

    def num_iterations(self) -> int:
        return len(self.snapshots)

    def get_last_k(self, k: int) -> List[Dict[int, Dict[str, str]]]:
        if k > len(self.snapshots):
            raise ValueError(
                f"Requested {k} snapshots, but only {len(self.snapshots)} available."
            )
        return self.snapshots[-k:]

# ---------------------------------------------------------------------
# Active Learning Metadata
# ---------------------------------------------------------------------

@dataclass
class ActiveLearningMetadata:
    feedback_texts: List[str]
    seed_indices: List[int]
    seed_proposal_factory: Optional[Callable[[int, str], DimensionLabelProposal]] = None

    records: List[Dict] = field(init=False)
    prediction_history: PredictionHistory = field(default_factory=PredictionHistory)

    def __post_init__(self):
        self.records = []

        for idx, text in enumerate(self.feedback_texts):
            seed = None
            if self.seed_proposal_factory and idx in self.seed_indices:
                seed = self.seed_proposal_factory(idx, text)

            self.records.append({
                "index": idx,
                "text": text,
                "seed_proposal": seed,
                "labeled": False,
                "labels": {},
                "confidences": {},
                "rationale": {},
                "evidence": [],
                "source": None,
                "model_id": None,
                "label_source": None,
            })

    # ------------------------
    # Read-only accessors
    # ------------------------

    def unlabeled_indices(self) -> List[int]:
        return [r["index"] for r in self.records if not r["labeled"]]

    def labeled_indices(self) -> List[int]:
        return [r["index"] for r in self.records if r["labeled"]]

    def get_record(self, idx: int) -> Dict:
        return self.records[idx]

    # ------------------------
    # Mutation
    # ------------------------

    def apply_labels(
        self,
        idx: int,
        labels: Dict[str, str],
        confidences: Dict[str, float],
        rationale: Optional[Dict[str, str]] = None,
        evidence: Optional[List[str]] = None,
        source: Optional[str] = None,
        model_id: Optional[str] = None,
    ) -> None:
        record = self.records[idx]
        record["labels"] = labels
        record["confidences"] = confidences
        record["rationale"] = rationale or {}
        record["evidence"] = evidence or []
        record["source"] = source
        record["model_id"] = model_id
        record["labeled"] = True
        record["label_source"] = "seed"

    def done(self) -> bool:
        return all(r["labeled"] for r in self.records)

    # ------------------------
    # Persistence
    # ------------------------

    def _make_json_serializable(self, obj: Any) -> Any:
        """
        Recursively convert non-serializable objects to primitives.
        - LabelValue -> its `.value`
        - DimensionLabelProposal -> convert labels, confidences, rationale, evidence, source, model_id
        """
        from curation.dimension_label_proposal import LabelValue, DimensionLabelProposal

        if isinstance(obj, LabelValue):
            return obj.value
        elif isinstance(obj, DimensionLabelProposal):
            return {
                "labels": {k: self._make_json_serializable(v) for k, v in obj.labels.items()},
                "confidences": obj.confidences,
                "rationale": obj.rationale,
                "evidence": obj.evidence,
                "source": obj.source,
                "model_id": obj.model_id,
            }
        elif isinstance(obj, dict):
            return {k: self._make_json_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._make_json_serializable(v) for v in obj]
        else:
            return obj

    def save(self, path: str):
        """
        Save metadata to a JSON file safely, converting any non-serializable objects
        (LabelValue, DimensionLabelProposal, etc.) into JSON-compatible primitives.
        """
        serializable_records = [self._make_json_serializable(r) for r in self.records]

        import json
        with open(path, "w", encoding="utf-8") as f:
            json.dump(serializable_records, f, ensure_ascii=False, indent=2)

    @classmethod
    def load(cls, path: str) -> "ActiveLearningMetadata":
        import json
        from curation.dimension_label_proposal import DimensionLabelProposal, LabelValue

        with open(path, "r", encoding="utf-8") as f:
            payload = json.load(f)

        obj = cls.__new__(cls)

        # Detect if payload is a list (old format) or dict
        if isinstance(payload, list):
            records_json = payload
            obj.prediction_history = PredictionHistory()
        else:
            records_json = payload.get("records", [])
            obj.prediction_history = PredictionHistory(
                snapshots=payload.get("prediction_history", [])
            )

        # Reconstruct DimensionLabelProposal objects in records
        records = []
        for r in records_json:
            # If labels exist, convert to DimensionLabelProposal
            labels = r.get("labels", {})
            confidences = r.get("confidences", {})
            rationale = r.get("rationale", {})
            evidence = r.get("evidence", [])
            source = r.get("source")
            model_id = r.get("model_id")

            proposal = None
            if labels:
                # Wrap labels with LabelValue if needed
                labels_wrapped = {
                    k: v if isinstance(v, LabelValue) else LabelValue(v)
                    for k, v in labels.items()
                }
                proposal = DimensionLabelProposal(
                    labels=labels_wrapped,
                    confidences=confidences,
                    rationale=rationale,
                    evidence=evidence,
                    source=source,
                    model_id=model_id
                )

            r["seed_proposal"] = proposal
            records.append(r)

        obj.records = records

        # Initialize other fields to safe defaults
        obj.feedback_texts = [r.get("text", "") for r in obj.records]
        obj.seed_indices = []
        obj.seed_proposal_factory = None

        return obj

    # ------------------------
    # Convenience
    # ------------------------

    def get_labels_as_dict(self, idx: int) -> dict:
        record = self.records[idx]
        return {k: (v.value if isinstance(v, LabelValue) else v) for k, v in record.get("labels", {}).items()}

    def mark_as_labeled(self, indices, proposals):
        for idx, proposal in zip(indices, proposals):
            self.records[idx]["labeled"] = True
            self.records[idx]["labels"] = {
                k: v if isinstance(v, LabelValue) else LabelValue(v)
                for k, v in proposal.labels.items()
            }
            self.records[idx]["confidences"] = proposal.confidences
            self.records[idx]["rationale"] = proposal.rationale
            self.records[idx]["evidence"] = proposal.evidence
            self.records[idx]["source"] = proposal.source
            self.records[idx]["model_id"] = proposal.model_id
