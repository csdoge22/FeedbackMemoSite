# curation/query/query_strategies.py
from typing import List, TypedDict, Optional
import logging
import numpy as np

logger = logging.getLogger(__name__)


class Record(TypedDict, total=False):
    labeled: bool
    confidences: Optional[dict]
    mc_probs: Optional[List[np.ndarray]]  # Each element shape=(C,)
    embedding: Optional[np.ndarray]


# -------------------------------
# Least Confidence Sampling
# -------------------------------
def least_confidence_sampling(records: List[Record], n: int) -> List[int]:
    model_confidences = np.array([
        min(r.get("confidences", {}).values()) if r.get("confidences") else 0.0
        for r in records
    ])
    labeled_mask = np.array([r.get("labeled", False) for r in records])
    model_confidences[labeled_mask] = np.inf
    selected = np.argsort(model_confidences)[:n].tolist()
    logger.info("[LeastConfidence] Selected indices: %s", selected)
    return selected


# -------------------------------
# BALD Sampling (vectorized)
# -------------------------------
def bald_sampling(records: List[Record], n: int) -> List[int]:
    unlabeled_mask = np.array([not r.get("labeled", False) for r in records])
    unlabeled_indices = np.where(unlabeled_mask)[0]

    if len(unlabeled_indices) == 0:
        return []

    # Collect MC probability arrays
    mc_list = [np.stack(records[i]["mc_probs"]) for i in unlabeled_indices if records[i].get("mc_probs")]
    if not mc_list:
        return []

    # Stack into shape (num_unlabeled, T, C)
    mc_probs_stack = np.stack(mc_list, axis=0)
    mean_probs = mc_probs_stack.mean(axis=1)
    predictive_entropy = -np.sum(mean_probs * np.log(mean_probs + 1e-12), axis=1)
    expected_entropy = -np.mean(np.sum(mc_probs_stack * np.log(mc_probs_stack + 1e-12), axis=2), axis=1)
    bald_scores_array = predictive_entropy - expected_entropy

    # Map back to full record indices
    bald_scores = np.zeros(len(records))
    bald_scores[unlabeled_indices[:len(bald_scores_array)]] = bald_scores_array
    bald_scores[~unlabeled_mask] = -1.0
    bald_scores /= bald_scores.max() + 1e-12

    selected = np.argsort(-bald_scores)[:n].tolist()
    logger.info("[BALD] Selected indices: %s", selected)
    return selected


# -------------------------------
# Greedy Coreset Sampling (vectorized)
# -------------------------------
def greedy_coreset_sampling(records: List[Record], n: int) -> List[int]:
    embeddings = np.array([r.get("embedding") if r.get("embedding") is not None else np.zeros(1) for r in records])
    labeled_mask = np.array([r.get("labeled", False) for r in records])
    unlabeled_mask = ~labeled_mask
    unlabeled_indices = np.where(unlabeled_mask)[0]

    if len(unlabeled_indices) == 0:
        return []

    labeled_indices = np.where(labeled_mask)[0]

    if len(labeled_indices) == 0:
        # Cold start
        selected = unlabeled_indices[:n].tolist()
        logger.info("[Coreset] Cold start selection: %s", selected)
        return selected

    # Distance matrix: (num_unlabeled, num_labeled)
    dist_matrix = np.linalg.norm(
        embeddings[unlabeled_indices][:, None, :] - embeddings[labeled_indices][None, :, :],
        axis=2
    )
    min_distances = dist_matrix.min(axis=1)

    # Top-n indices
    top_indices_local = np.argpartition(-min_distances, n-1)[:n]
    selected = unlabeled_indices[top_indices_local[np.argsort(-min_distances[top_indices_local])]].tolist()
    logger.info("[Coreset] Selected indices: %s", selected)
    return selected


# -------------------------------
# Hybrid: Coreset + BALD (fully vectorized)
# -------------------------------
def hybrid_coreset_bald_sampling(records: List[Record], n: int, lambda_t: float) -> List[int]:
    lambda_t = float(np.clip(lambda_t, 0.0, 1.0))
    num_records = len(records)
    embeddings = np.array([r.get("embedding") if r.get("embedding") is not None else np.zeros(1) for r in records])
    labeled_mask = np.array([r.get("labeled", False) for r in records])
    unlabeled_mask = ~labeled_mask
    unlabeled_indices = np.where(unlabeled_mask)[0]

    if len(unlabeled_indices) == 0:
        return []

    labeled_indices = np.where(labeled_mask)[0]

    # -----------------------
    # Vectorized Coreset scores
    # -----------------------
    coreset_scores = np.zeros(num_records)
    if len(labeled_indices) == 0:
        coreset_scores[unlabeled_indices] = 1.0
    else:
        dists = np.linalg.norm(
            embeddings[unlabeled_indices][:, None, :] - embeddings[labeled_indices][None, :, :],
            axis=2
        )
        min_distances = dists.min(axis=1)
        coreset_scores[unlabeled_indices] = min_distances / (min_distances.max() + 1e-12)

    # -----------------------
    # Vectorized BALD scores
    # -----------------------
    bald_scores = np.zeros(num_records)
    mc_list = [np.stack(records[i]["mc_probs"]) for i in unlabeled_indices if records[i].get("mc_probs")]
    if mc_list:
        mc_probs_stack = np.stack(mc_list, axis=0)
        mean_probs = mc_probs_stack.mean(axis=1)
        predictive_entropy = -np.sum(mean_probs * np.log(mean_probs + 1e-12), axis=1)
        expected_entropy = -np.mean(np.sum(mc_probs_stack * np.log(mc_probs_stack + 1e-12), axis=2), axis=1)
        bald_scores_array = predictive_entropy - expected_entropy
        bald_scores[unlabeled_indices[:len(bald_scores_array)]] = bald_scores_array
        bald_scores /= bald_scores.max() + 1e-12
    bald_scores[~unlabeled_mask] = -1.0

    # -----------------------
    # Combine
    # -----------------------
    combined_scores = lambda_t * coreset_scores + (1.0 - lambda_t) * bald_scores
    combined_scores[labeled_mask] = -1.0
    selected = np.argsort(-combined_scores)[:n].tolist()
    logger.info("[Hybrid] λ=%.3f | Selected indices: %s", lambda_t, selected)
    return selected
