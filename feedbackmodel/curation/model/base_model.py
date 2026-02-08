"""
Model interface for Active Learning.
Provides a unified API for:
- ML models
- LLM labeling
- Confidence updates
"""

from abc import ABC, abstractmethod
from typing import List, Dict

class BaseModel(ABC):
    """
    Abstract interface for predictive models.
    All models must implement `predict`.
    """

    @abstractmethod
    def predict(self, texts: List[str]) -> Dict[str, List[str]]:
        """
        Predict multi-dimensional labels for each text.

        Parameters
        ----------
        texts : List[str]
            Texts to predict on

        Returns
        -------
        Dict[str, List[str]]
            Keys: dimension names (e.g., severity, urgency, impact)
            Values: list of labels for each text
        """
        pass

# Example: classical ML model wrapper
class SklearnModel(BaseModel):
    def __init__(self, model, vectorizer, dimensions: List[str]):
        self.model = model
        self.vectorizer = vectorizer
        self.dimensions = dimensions  # ['severity', 'urgency', 'impact']

    def predict(self, texts: List[str]) -> Dict[str, List[str]]:
        X = self.vectorizer.transform(texts)
        # Assume model.predict returns shape (n_samples, n_dimensions)
        predictions = self.model.predict(X)
        result = {dim: [] for dim in self.dimensions}
        for i, dim in enumerate(self.dimensions):
            result[dim] = predictions[:, i].tolist()
        return result

# Example: LLM wrapper
class LLMModel(BaseModel):
    def __init__(self, llm_oracle, dimensions: List[str]):
        self.llm_oracle = llm_oracle
        self.dimensions = dimensions

    def predict(self, texts: List[str]) -> Dict[str, List[str]]:
        result = {dim: [] for dim in self.dimensions}
        for text in texts:
            prediction = self.llm_oracle.label(text)
            # Expect prediction to be a dict {dim: label}
            for dim in self.dimensions:
                result[dim].append(prediction.get(dim, None))
        return result
