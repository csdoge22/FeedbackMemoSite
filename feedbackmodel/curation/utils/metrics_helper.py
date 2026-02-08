# curation/utils/metrics_helper.py
from typing import Dict, List, Any
import numpy as np
from sklearn.metrics import cohen_kappa_score


def compute_per_dimension_kappa(
    prev_snapshot: List[Dict[int, Dict[str, Any]]],
    curr_snapshot: List[Dict[int, Dict[str, Any]]],
    dimensions: List[str],
) -> Dict[str, float]:
    """
    Compute Cohen's Kappa for each dimension between two snapshots.

    Missing or None values are treated as "__unknown__".
    """
    placeholder = "__unknown__"
    per_dim_kappa: Dict[str, float] = {}

    # Convert snapshots to index -> dim -> label mapping
    prev_labels = {
        idx: {dim: (label if label is not None else placeholder)
              for dim, label in labels.items()}
        for snapshot in prev_snapshot
        for idx, labels in snapshot.items()
    }

    curr_labels = {
        idx: {dim: (label if label is not None else placeholder)
              for dim, label in labels.items()}
        for snapshot in curr_snapshot
        for idx, labels in snapshot.items()
    }

    # Only compute for indices present in both snapshots
    common_indices = set(prev_labels.keys()) & set(curr_labels.keys())

    for dim in dimensions:
        y_prev = [prev_labels[i][dim] for i in common_indices]
        y_curr = [curr_labels[i][dim] for i in common_indices]
        per_dim_kappa[dim] = cohen_kappa_score(y_prev, y_curr)

    return per_dim_kappa
