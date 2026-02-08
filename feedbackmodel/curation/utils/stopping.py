# curation/utils/stopping.py
from dataclasses import dataclass
from typing import Dict, List, Any
import numpy as np
from sklearn.metrics import cohen_kappa_score


@dataclass(frozen=True)
class StoppingConfig:
    """
    Configuration for active learning stopping criterion.
    """
    min_iterations: int
    patience: int
    window_size: int
    mean_kappa_threshold: float = 0.99
    floor_kappa_threshold: float = 0.95


class StoppingController:
    """
    Tracks prediction snapshots and computes per-dimension kappa to determine
    if active learning predictions have stabilized.
    """

    def __init__(self, config: StoppingConfig, dimensions: List[str]):
        self.config = config
        self.dimensions = dimensions
        self.prediction_history: List[Dict[int, Dict[str, Any]]] = []
        self.stable_counter = 0
        self.last_per_dim_kappa: Dict[str, float] = {dim: np.nan for dim in dimensions}

    @staticmethod
    def _safe_kappa(y1: List[Any], y2: List[Any]) -> float:
        if len(y1) < 2 or len(y1) != len(y2):
            return np.nan
        labels_1, labels_2 = set(y1), set(y2)
        if len(labels_1) < 2 or len(labels_2) < 2:
            return np.nan
        labels = sorted(labels_1 | labels_2)
        try:
            return cohen_kappa_score(y1, y2, labels=labels)
        except ValueError:
            return np.nan

    def update(self, predictions: Dict[int, Dict[str, Any]]) -> bool:
        """
        Add a snapshot and check if active learning should stop.
        """
        self.prediction_history.append(predictions)

        if len(self.prediction_history) < self.config.window_size:
            return False

        # Compute per-dimension kappas over the window
        window = self.prediction_history[-self.config.window_size:]
        per_dim_kappas: Dict[str, List[float]] = {dim: [] for dim in self.dimensions}

        for i in range(len(window) - 1):
            for dim in self.dimensions:
                y1 = [window[i][idx][dim] for idx in sorted(window[i].keys()) if dim in window[i][idx]]
                y2 = [window[i + 1][idx][dim] for idx in sorted(window[i + 1].keys()) if dim in window[i + 1][idx]]
                k = self._safe_kappa(y1, y2)
                if not np.isnan(k):
                    per_dim_kappas[dim].append(k)

        dim_means = []
        for dim, ks in per_dim_kappas.items():
            if ks:
                mean_k = float(np.mean(ks))
                self.last_per_dim_kappa[dim] = mean_k
                dim_means.append(mean_k)
                if mean_k < self.config.floor_kappa_threshold:
                    self.stable_counter = 0
                    return False
            else:
                self.last_per_dim_kappa[dim] = np.nan

        if not dim_means:
            return False

        overall_mean = float(np.nanmean(dim_means))
        self.stable_counter = self.stable_counter + 1 if overall_mean >= self.config.mean_kappa_threshold else 0

        return self.stable_counter >= self.config.patience

    def reset(self) -> None:
        """
        Clear prediction history and stability counter.
        """
        self.prediction_history.clear()
        self.stable_counter = 0
        self.last_per_dim_kappa = {dim: np.nan for dim in self.dimensions}
