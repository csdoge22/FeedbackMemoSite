from typing import Dict

def compute_priority(labels: Dict[str, str]) -> str:
    """
    Derive a single priority from dimension-level labels.
    Uses simple heuristic: high > medium > low
    """
    if "high" in labels.values():
        return "high"
    elif "medium" in labels.values():
        return "medium"
    else:
        return "low"
