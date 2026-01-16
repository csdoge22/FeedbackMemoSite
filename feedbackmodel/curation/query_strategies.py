# curation/query_strategies.py
import random
from typing import List, Dict

def random_sampling(records: List[Dict], n: int) -> List[int]:
    """
    Select n random indices from unlabeled feedback records.
    """
    unlabeled = [i for i, r in enumerate(records) if not r["labeled"]]
    return random.sample(unlabeled, min(n, len(unlabeled)))

def least_confidence_sampling(records: List[Dict], n: int) -> List[int]:
    """
    Select `n` feedback items with lowest average confidence.
    Skips any items that are already labeled (including seeds).
    - records: list of metadata dicts (from ActiveLearningMetadata.records)
    - n: batch size
    Returns: list of indices to label
    """
    unlabeled_confidences = []

    for i, r in enumerate(records):
        if r["labeled"]:
            continue  # skip seeds and already labeled
        # Compute average confidence; assume 0.5 if no confidences yet
        conf_dict = r.get("confidences", {})
        avg_conf = sum(conf_dict.values()) / max(len(conf_dict), 1)
        unlabeled_confidences.append((i, avg_conf))

    # Sort by lowest confidence
    unlabeled_confidences.sort(key=lambda x: x[1])
    return [i for i, _ in unlabeled_confidences[:n]]  # return up to n indices

def select_bald_sampling(records: List[Dict], n: int) -> List[int]:
    """
    Placeholder for BALD acquisition function (uncertainty in predictions).
    Currently falls back to least confidence.
    """
    return least_confidence_sampling(records, n)
