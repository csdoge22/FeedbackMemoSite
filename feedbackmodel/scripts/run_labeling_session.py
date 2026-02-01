# scripts/run_labeling_session.py

import logging
import math
import time
from pathlib import Path
from typing import Dict, List, Tuple
import json
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.metrics import f1_score
import os

from dataset.analysis.dataset_clustering import run_clustering_pipeline
from dataset.processing.load_splits import load_split
from curation.metadata.metadata import ActiveLearningMetadata
from curation.labeling.human_labeling import HumanLabeling
from curation.model.model_confidence_updater import ModelConfidenceUpdater

# 🔁 QUERY STRATEGIES
from curation.query.query_strategies import (
    least_confidence_sampling,
    greedy_coreset_sampling,
    bald_sampling,
    hybrid_coreset_bald_sampling,
)

from curation.utils.rag_client import RAGClient, CollectionClient
from curation.seeds.seed_factory import seeded_seed_proposal
from curation.labeling.llm_labeling import LLMOracle
from curation.utils.stopping import StoppingConfig, StoppingController
from curation.utils.metrics import ALMetricsTracker
from curation.artifacts.saver import save_all_artifacts
from curation.artifacts.model_artifact import ModelArtifact
from dataset.embedding.database_client import EmbeddingCacheClient

# -----------------------------
# CONFIG
# -----------------------------
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"

BATCH_SIZE = 5
MODEL_ID = "weak_llm_v1"
SAVE_EVERY_ITERATION = True
ARTIFACT_DIR = Path("model_artifact")
LOG_FILE = Path("logs/run_labeling_session.log")
METRICS_LOG_FILE = Path("logs/active_learning_metrics.log")
DIMENSIONS = ["severity", "urgency", "impact"]

# Hybrid λ(t) scheduler
CORESET_WARMUP_ITERS = 2
LAMBDA_DECAY = 0.15
MIN_LAMBDA = 0.0

# -----------------------------
# LOGGING
# -----------------------------
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_FILE, mode="w"),
    ],
)
logger = logging.getLogger(__name__)

# -----------------------------
# LLM ORACLE
# -----------------------------
llm_oracle = LLMOracle(model_name="mistralai/mistral-7b-instruct-v0.3")

def llm_call_fn(prompt: str) -> str:
    return llm_oracle.label(prompt)

# -----------------------------
# METRICS HELPERS
# -----------------------------
def compute_per_dimension_f1(y_true, y_pred) -> Dict[str, float]:
    scores = {}
    for dim in DIMENSIONS:
        try:
            scores[dim] = f1_score(y_true[dim], y_pred[dim], average="macro", zero_division=0)
        except Exception:
            scores[dim] = 0.0
    return scores

def compute_macro_f1(per_dim_f1: Dict[str, float]) -> float:
    return sum(per_dim_f1.values()) / len(per_dim_f1) if per_dim_f1 else 0.0

def replace_nan_with_none(obj):
    if isinstance(obj, dict):
        return {k: replace_nan_with_none(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [replace_nan_with_none(v) for v in obj]
    if isinstance(obj, float) and math.isnan(obj):
        return None
    return obj


# -----------------------------
# ARTIFACT HELPERS
# -----------------------------
def wrap_artifacts(metadata: ActiveLearningMetadata, model_updater: ModelConfidenceUpdater) -> Dict[str, ModelArtifact]:
    artifacts = {}
    for dim in DIMENSIONS:
        if not model_updater.is_fitted[dim]:
            continue
        artifacts[dim] = ModelArtifact(
            model=model_updater.get_model(dim),
            vectorizer=model_updater.get_vectorizer(),
            labels=model_updater.get_model(dim).classes_.tolist(),
            metadata={
                "dimension": dim,
                "num_training_examples": len(metadata.labeled_indices()),
                "created_at": time.time(),
            }
        )
    return artifacts


# -----------------------------
# QUERY STRATEGY HELPERS
# -----------------------------
def compute_lambda(iteration: int) -> float:
    return max(MIN_LAMBDA, 1.0 - (iteration - CORESET_WARMUP_ITERS) * LAMBDA_DECAY)

def select_batch_indices(
    metadata: ActiveLearningMetadata,
    iteration: int,
    strategy: str = "hybrid",
    batch_size: int = BATCH_SIZE
) -> List[int]:
    if strategy == "least_confidence":
        logger.info("[Query] Using Least Confidence Sampling")
        return least_confidence_sampling(metadata.records, batch_size)
    elif strategy == "coreset":
        logger.info("[Query] Using Greedy Coreset Sampling")
        return greedy_coreset_sampling(metadata.records, batch_size)
    elif strategy == "bald":
        logger.info("[Query] Using BALD Sampling")
        return bald_sampling(metadata.records, batch_size)
    elif strategy == "hybrid":
        if iteration <= CORESET_WARMUP_ITERS:
            logger.info("[Query] Using Greedy Coreset (warm-up)")
            return greedy_coreset_sampling(metadata.records, batch_size)
        else:
            lambda_t = compute_lambda(iteration)
            logger.info("[Query] Using Hybrid Coreset + BALD (λ=%.3f)", lambda_t)
            return hybrid_coreset_bald_sampling(metadata.records, batch_size, lambda_t)
    else:
        raise ValueError(f"Unknown query strategy: {strategy}")


# -----------------------------
# MAIN ACTIVE LEARNING LOOP
# -----------------------------
def main(strategy: str = "hybrid"):
    # Create embedding cache + RAG client (caching handled internally)
    embedding_cache_client = EmbeddingCacheClient(split="train", top_k=5)
    rag_client = RAGClient(collection_client=embedding_cache_client, top_k=5)

    # -----------------------------
    # Run clustering and get seeds
    # -----------------------------
    outputs = run_clustering_pipeline(
        split="train",
        initial_seed_count=50,
        plot=False,
        embedding_cache=embedding_cache_client
    )
    df = outputs["df"]
    seed_indices = outputs["seed_indices"]

    # -----------------------------
    # Initialize metadata for active learning
    # -----------------------------
    metadata = ActiveLearningMetadata(
        feedback_texts=df["feedback_text"].tolist(),
        seed_indices=seed_indices,
        seed_proposal_factory=seeded_seed_proposal,
    )

    # Mark initial seeds as labeled
    for idx in seed_indices:
        seed = metadata.records[idx]["seed_proposal"]
        if seed:
            metadata.mark_as_labeled([idx], [seed])

    # -----------------------------
    # Human labeling setup
    # -----------------------------
    labeling = HumanLabeling(metadata, rag_client, llm_call_fn, embedding_cache=embedding_cache_client)
    model_updater = ModelConfidenceUpdater()

    stopper = StoppingController(
        StoppingConfig(
            min_iterations=2,
            patience=1,
            window_size=2,
            mean_kappa_threshold=0.99,
            floor_kappa_threshold=0.95
        ),
        DIMENSIONS
    )

    metrics = ALMetricsTracker(METRICS_LOG_FILE)

    stop_df = load_split("stop_labeled")
    test_df = load_split("test_labeled")
    stop_texts = stop_df["feedback_text"].tolist()
    test_texts = test_df["feedback_text"].tolist()
    true_test_labels = {d: test_df[d].tolist() for d in DIMENSIONS}

    # -----------------------------
    # Initial model fit
    # -----------------------------
    model_updater.fit(metadata)

    iteration = 0
    while not metadata.done():
        iteration += 1
        logger.info(f"[Iteration {iteration}] Starting")

        # Fit model and update confidences
        model_updater.fit(metadata)
        model_updater.update_unlabeled_confidences(metadata)

        # -----------------------------
        # Select batch for labeling
        # -----------------------------
        batch_indices = select_batch_indices(
            metadata, iteration, strategy=strategy, batch_size=BATCH_SIZE
        )
        if not batch_indices:
            logger.info("[Labeling] No unlabeled items left")
            break

        labeling.label_batch(batch_indices, MODEL_ID)

        # -----------------------------
        # Save artifacts per iteration
        # -----------------------------
        if SAVE_EVERY_ITERATION:
            artifacts = wrap_artifacts(metadata, model_updater)
            save_all_artifacts(artifacts, artifact_dir=ARTIFACT_DIR)

        # -----------------------------
        # Stopping check using STOP set
        # -----------------------------
        stop_preds = model_updater.predict(stop_texts)
        stop_snapshot = {i: {d: stop_preds[d][i] for d in DIMENSIONS} for i in range(len(stop_texts))}
        if stopper.update(stop_snapshot):
            logger.info("[Stopping] Predictions stabilized on STOP set")
            break

    # -----------------------------
    # Final save
    # -----------------------------
    artifacts = wrap_artifacts(metadata, model_updater)
    save_all_artifacts(artifacts, artifact_dir=ARTIFACT_DIR)
    metadata.save("metadata.json")
    logger.info("[Done] Labeling complete")


if __name__ == "__main__":
    main(strategy="hybrid")
