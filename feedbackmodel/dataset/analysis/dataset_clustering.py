# dataset/analysis/dataset_clustering.py
import os
from typing import Any, Dict
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import umap
import logging

from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

from dataset.processing.dataset_loader import load_dataset
from dataset.processing.preprocessing import preprocess_text_series
from dataset.embedding.embedding_cache_client import EmbeddingCacheClient

logger = logging.getLogger(__name__)

# ============================================================
# Configuration
# ============================================================
MAX_K = 15
RANDOM_STATE = 42

UMAP_N_NEIGHBORS = 15 
UMAP_MIN_DIST = 0.1

PLOT_DIR = os.path.join(os.path.dirname(__file__), "plots")
os.makedirs(PLOT_DIR, exist_ok=True)

# ============================================================
# Dimensionality Reduction (UMAP)
# ============================================================
def reduce_dimensionality(embeddings):
    reducer = umap.UMAP(
        n_neighbors=UMAP_N_NEIGHBORS,
        min_dist=UMAP_MIN_DIST,
        random_state=RANDOM_STATE,
    )
    embeddings_2d = reducer.fit_transform(embeddings)
    return embeddings_2d, reducer

# ============================================================
# Optimal K Selection
# ============================================================
def find_optimal_k(embeddings, max_k=MAX_K):
    wcss = []
    silhouettes = []

    ks = range(2, max_k + 1)
    for k in ks:
        kmeans = KMeans(n_clusters=k, random_state=RANDOM_STATE)
        labels = kmeans.fit_predict(embeddings)
        wcss.append(kmeans.inertia_)
        silhouettes.append(silhouette_score(embeddings, labels))

    # Plot Elbow + Silhouette
    plt.figure(figsize=(12, 5))
    plt.subplot(1, 2, 1)
    plt.plot(ks, wcss, marker="o")
    plt.title("Elbow Method (WCSS)")
    plt.xlabel("k")
    plt.ylabel("WCSS")

    plt.subplot(1, 2, 2)
    plt.plot(ks, silhouettes, marker="o")
    plt.title("Silhouette Scores")
    plt.xlabel("k")
    plt.ylabel("Score")

    plt.tight_layout()
    path = os.path.join(PLOT_DIR, "k_selection.png")
    plt.savefig(path, dpi=300)
    plt.close()

    optimal_k = ks[np.argmax(silhouettes)]
    print(f"[KMeans] Suggested optimal k = {optimal_k}")
    return optimal_k

# ============================================================
# KMeans Clustering
# ============================================================
def cluster_embeddings(embeddings, n_clusters):
    kmeans = KMeans(
        n_clusters=n_clusters,
        random_state=RANDOM_STATE,
        n_init="auto",
    )
    labels = kmeans.fit_predict(embeddings)
    centroids = kmeans.cluster_centers_
    return labels, centroids

# ============================================================
# Seed Selection
# ============================================================
def log_weighted_round_robin_seed_selection(labels, embeddings, centroids, num_seeds):
    cluster_ids = np.unique(labels)
    seed_indices = []

    # Step 1: Centroid-nearest points
    for cluster_id in cluster_ids:
        cluster_idx = np.where(labels == cluster_id)[0]
        cluster_emb = embeddings[cluster_idx]
        centroid = centroids[cluster_id]
        distances = np.linalg.norm(cluster_emb - centroid, axis=1)
        nearest_idx = cluster_idx[np.argmin(distances)]
        seed_indices.append(nearest_idx)

    # Step 2: Additional seeds by log-weighted round robin
    remaining_seeds = max(0, num_seeds - len(seed_indices))
    if remaining_seeds > 0:
        cluster_counts = {cid: np.sum(labels == cid) for cid in cluster_ids}
        log_weights = {cid: np.log(count + 1) for cid, count in cluster_counts.items()}

        weighted_clusters = []
        for cid, weight in log_weights.items():
            repeat = int(np.ceil(weight))
            weighted_clusters.extend([cid] * repeat)

        np.random.shuffle(weighted_clusters)
        added = 0
        idx_in_cluster = {cid: np.where(labels == cid)[0].tolist() for cid in cluster_ids}
        while added < remaining_seeds and weighted_clusters:
            for cid in weighted_clusters:
                candidates = [i for i in idx_in_cluster[cid] if i not in seed_indices]
                if candidates:
                    seed_indices.append(candidates[0])
                    added += 1
                    if added >= remaining_seeds:
                        break

    return seed_indices

# ============================================================
# Visualization
# ============================================================
def save_cluster_plot(embeddings_2d, labels, centroids_2d, split, seed_indices=None):
    plt.figure(figsize=(10, 8))
    plt.scatter(
        embeddings_2d[:, 0],
        embeddings_2d[:, 1],
        c=labels,
        cmap="tab20",
        s=10,
        alpha=0.6,
    )
    plt.scatter(
        centroids_2d[:, 0],
        centroids_2d[:, 1],
        c="black",
        marker="X",
        s=180,
        edgecolors="white",
        linewidths=1.5,
        label="Centroids",
    )

    if seed_indices is not None and len(seed_indices) > 0:
        plt.scatter(
            embeddings_2d[seed_indices, 0],
            embeddings_2d[seed_indices, 1],
            c="red",
            marker="o",
            s=80,
            edgecolors="yellow",
            linewidths=1.5,
            label="Selected Seeds",
        )

    plt.legend()
    plt.title(f"UMAP Clusters with Centroids ({split})")
    plt.xlabel("UMAP-1")
    plt.ylabel("UMAP-2")

    path = os.path.join(PLOT_DIR, f"{split}_clusters.png")
    plt.savefig(path, dpi=300)
    plt.close()
    print(f"[Saved] Cluster plot → {path}")

# ============================================================
# Reusable Clustering Pipeline (use external EmbeddingCache)
# ============================================================
def run_clustering_pipeline(
    split: str = "train",
    initial_seed_count: int = 50,
    plot: bool = True,
    embedding_cache: EmbeddingCacheClient | None = None,
) -> Dict[str, Any]:
    """
    Clustering pipeline using cached MiniLM embeddings.
    """

    if embedding_cache is None:
        embedding_cache = EmbeddingCacheClient(split=split)

    # Load dataset ONCE
    df = load_dataset(split)
    texts = preprocess_text_series(df["feedback_text"])

    # Encode texts (no caching logic here)
    embeddings = embedding_cache.encode_texts(texts)
    logger.info(f"[Clustering] Encoded {len(embeddings)} texts")

    # Dimensionality reduction
    embeddings_2d, reducer = reduce_dimensionality(embeddings)

    # K selection
    optimal_k = find_optimal_k(embeddings)

    # Clustering
    labels, centroids = cluster_embeddings(embeddings, optimal_k)
    centroids_2d = reducer.transform(centroids)

    # Seed selection
    seed_indices = log_weighted_round_robin_seed_selection(
        labels, embeddings, centroids, initial_seed_count
    )

    if plot:
        save_cluster_plot(
            embeddings_2d, labels, centroids_2d, split, seed_indices
        )

    return {
        "df": df,
        "embeddings": embeddings,
        "labels": labels,
        "centroids": centroids,
        "seed_indices": seed_indices,
        "embeddings_2d": embeddings_2d,
        "centroids_2d": centroids_2d,
    }


# ============================================================
# Utility
# ============================================================
def get_distribution(labels):
    unique, counts = np.unique(labels, return_counts=True)
    return dict(zip(unique.tolist(), counts.tolist()))

# ============================================================
# Script Entry
# ============================================================
if __name__ == "__main__":
    outputs = run_clustering_pipeline("train", initial_seed_count=50, plot=True)
    print("\nSeed texts:")
    for i, text in enumerate(outputs["df"].iloc[outputs["seed_indices"]]["feedback_text"]):
        print(f"[Seed {i}] {text}")
