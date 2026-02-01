from typing import Dict, List, Any
from sklearn.metrics import f1_score

from curation.evaluation.base_evaluator import BaseEvaluator


class ModelEvaluator(BaseEvaluator):
    def __init__(self, placeholder: str = "__unknown__"):
        self.placeholder = placeholder

    def _macro_f1(self, y_true: List[Any], y_pred: List[Any]) -> float:
        y_true_clean = [
            v if v is not None else self.placeholder for v in y_true
        ]
        y_pred_clean = [
            v if v is not None else self.placeholder for v in y_pred
        ]

        try:
            return float(
                f1_score(
                    y_true_clean,
                    y_pred_clean,
                    average="macro",
                    zero_division=0,
                )
            )
        except Exception:
            return 0.0

    def evaluate(
        self,
        truth: Dict[str, List[Any]],
        predictions: Dict[str, List[Any]],
        dimensions: List[str],
    ) -> Dict[str, float]:
        return {
            dim: self._macro_f1(
                truth.get(dim, []),
                predictions.get(dim, []),
            )
            for dim in dimensions
        }
