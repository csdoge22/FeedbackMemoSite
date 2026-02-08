from typing import Dict, List, Any
from sklearn.metrics import cohen_kappa_score

from curation.evaluation.base_evaluator import BaseEvaluator


class KappaEvaluator(BaseEvaluator):
    def __init__(self, placeholder: str = "__unknown__"):
        self.placeholder = placeholder

    def _safe_kappa(self, a: List[Any], b: List[Any]) -> float:
        if len(a) != len(b):
            raise ValueError("Prediction lists must have the same length")

        a_clean = [x if x is not None else self.placeholder for x in a]
        b_clean = [x if x is not None else self.placeholder for x in b]

        if len(set(a_clean)) == 1 and len(set(b_clean)) == 1:
            return 1.0 if a_clean[0] == b_clean[0] else 0.0

        try:
            return float(cohen_kappa_score(a_clean, b_clean))
        except Exception:
            return 0.0

    def evaluate(
        self,
        previous: Dict[str, List[Any]],
        current: Dict[str, List[Any]],
        dimensions: List[str],
    ) -> Dict[str, float]:
        return {
            dim: self._safe_kappa(
                previous.get(dim, []),
                current.get(dim, []),
            )
            for dim in dimensions
        }
