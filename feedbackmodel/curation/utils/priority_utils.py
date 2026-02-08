# curation/utils/priority_utils.py
from typing import Dict, Union


def compute_priority(
    dims: Dict[str, Union[str, float]],
    low_prop: float,
    med_prop: float,
    high_prop: float,
) -> float:
    """
    Compute a priority score between 0 and 1 from multi-dimensional labels.

    Accepts numeric values or string labels ('low', 'medium', 'high').
    """
    mapping = {"low": low_prop, "medium": med_prop, "high": high_prop}
    total = 0.0
    count = 0

    for v in dims.values():
        if isinstance(v, str):
            total += mapping.get(v.lower(), 0.0)
        else:
            total += float(v)
        count += 1

    return total / count if count > 0 else 0.0
