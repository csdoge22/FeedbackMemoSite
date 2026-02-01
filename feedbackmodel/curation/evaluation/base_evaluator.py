from abc import ABC, abstractmethod
from typing import Dict, List, Any


class BaseEvaluator(ABC):
    """
    Base class for all evaluators.
    Enforces a consistent 'dimension -> score' contract.
    """

    @abstractmethod
    def evaluate(
        self,
        left: Dict[str, List[Any]],
        right: Dict[str, List[Any]],
        dimensions: List[str],
    ) -> Dict[str, float]:
        pass
