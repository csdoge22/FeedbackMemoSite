# scripts/run_labeling_session.py

import logging
import math
import time
from pathlib import Path
from typing import Dict, List
import json
import os
from sklearn.metrics import f1_score
import argparse

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

from curation.utils.rag_client import RAGClient
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

BATCH_SIZE = 10
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
# ACTIVE LEARNING PIPELINE
# -----------------------------
def run_active_learning(strategy: str = "hybrid"):
    # Embedding cache + RAG client
    embedding_cache_client = EmbeddingCacheClient(split="train", top_k=5)
    rag_client = RAGClient(collection_client=embedding_cache_client, top_k=5)

    # Run clustering and get seeds
    outputs = run_clustering_pipeline(
        split="train",
        initial_seed_count=50,
        plot=False,
        embedding_cache=embedding_cache_client
    )
    df = outputs["df"]
    seed_indices = outputs["seed_indices"]

    # Initialize metadata
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

    labeling = HumanLabeling(
        metadata,
        rag_client,
        llm_call_fn,
        embedding_cache=embedding_cache_client,
    )
    model_updater = ModelConfidenceUpdater()

    stopper = StoppingController(
        StoppingConfig(
            min_iterations=2,
            patience=2,
            window_size=3,
            mean_kappa_threshold=0.90,
            floor_kappa_threshold=0.80,
        ),
        DIMENSIONS,
    )

    stop_df = load_split("stop_labeled")
    test_df = load_split("test_labeled")
    stop_texts = stop_df["feedback_text"].tolist()
    test_texts = test_df["feedback_text"].tolist()
    true_test_labels = {d: test_df[d].tolist() for d in DIMENSIONS}

    model_updater.fit(metadata)

    iteration = 0
    while not metadata.done():
        iteration += 1
        logger.info(f"[Iteration {iteration}] Starting")

        model_updater.fit(metadata)
        model_updater.update_unlabeled_confidences(metadata)

        batch_indices = select_batch_indices(
            metadata,
            iteration,
            strategy=strategy,
            batch_size=BATCH_SIZE,
        )
        if not batch_indices:
            break

        labeling.label_batch(batch_indices, MODEL_ID)
        logger.info(f"[Iteration {iteration}] Labeled batch indices: {batch_indices}")

        if SAVE_EVERY_ITERATION:
            artifacts = wrap_artifacts(metadata, model_updater)
            save_all_artifacts(artifacts, artifact_dir=ARTIFACT_DIR)

        test_preds = model_updater.predict(test_texts)
        per_dim_f1 = compute_per_dimension_f1(true_test_labels, test_preds)
        macro_f1 = compute_macro_f1(per_dim_f1)

        metrics_record = {
            "iteration": iteration,
            "batch_indices": batch_indices,
            "per_dimension_f1": replace_nan_with_none(per_dim_f1),
            "macro_f1": macro_f1,
            "num_labeled": len(metadata.labeled_indices()),
            "timestamp": time.time(),
        }
        with open(METRICS_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(metrics_record) + "\n")

        stop_preds = model_updater.predict(stop_texts)
        stop_snapshot = {
            i: {d: stop_preds[d][i] for d in DIMENSIONS}
            for i in range(len(stop_texts))
        }
        if stopper.update(stop_snapshot):
            logger.info("[Stopping] Predictions stabilized on STOP set")
            break

    artifacts = wrap_artifacts(metadata, model_updater)
    save_all_artifacts(artifacts, artifact_dir=ARTIFACT_DIR)
    metadata.save("metadata.json")
    logger.info("[Done] Active learning complete")

# -----------------------------
# MAIN ACTIVE LEARNING LOOP
# -----------------------------
# -----------------------------
# MAIN ENTRY POINT
# -----------------------------
def main(
    strategy: str = "hybrid",
):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--use_active_learning",
        action="store_true",
        help="Flag to indicate whether to use active learning",
    )
    parser.add_argument("--strategy", default=strategy, help="Strategy to use for active learning")
    args = parser.parse_args()

    if args.use_active_learning:
        run_active_learning(strategy=args.strategy)
    else:
        raise NotImplementedError(
            "Non-active learning mode is intentionally not implemented yet."
        )

if __name__ == "__main__":
    main(strategy="hybrid")
