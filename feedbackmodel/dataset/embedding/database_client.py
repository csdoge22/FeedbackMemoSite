# dataset/embedding/database_client.py

import os
import numpy as np
import chromadb
from chromadb.utils import embedding_functions as ef

from dataset.processing.dataset_loader import load_dataset
from dataset.embedding.embedding_generator import (
    encode_dataset_split,
    encode_texts,
)

# ------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------

BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "data", "chroma")
)
COLLECTION_NAME = "feedback_priority_rag"

# ------------------------------------------------------------------
# Identity Embedding Function
# ------------------------------------------------------------------

class IdentityEmbeddingFunction(ef.EmbeddingFunction):
    """
    Prevents Chroma from recomputing embeddings.
    Assumes embeddings are already vectors.
    """

    def __init__(self):
        super().__init__()

    def __call__(self, input):
        return input


# ------------------------------------------------------------------
# Collection Initialization
# ------------------------------------------------------------------

def initialize_collection(client: chromadb.PersistentClient):
    os.makedirs(BASE_DIR, exist_ok=True)

    existing = [c.name for c in client.list_collections()]
    if COLLECTION_NAME in existing:
        client.delete_collection(name=COLLECTION_NAME)
        print(f"Collection '{COLLECTION_NAME}' deleted.")

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=IdentityEmbeddingFunction(),
    )
    return collection


# ------------------------------------------------------------------
# Database Initialization
# ------------------------------------------------------------------

def initialize_db() -> chromadb.api.models.Collection:
    """ Loads the dataset, creates the vector DB, and populates it."""
    client = chromadb.PersistentClient(path=BASE_DIR)
    collection = initialize_collection(client)

    train_set = load_dataset("train")

    ids = [f"train_{fid}" for fid in train_set["feedback_id"]]
    documents = train_set["feedback_text"].tolist()

    # ✅ FIX: unpack properly
    _, embeddings = encode_dataset_split("train")

    metadatas = []
    for row in train_set.itertuples(index=False):
        metadatas.append({
            "split": "train",
            "category": str(getattr(row, "category", "")),
            "source_context": str(getattr(row, "source_context", "")),
            "actionability_hint": str(getattr(row, "actionability_hint", "")),
        })

    collection.add(
        ids=ids,
        documents=documents,
        embeddings=embeddings,  # now correct
        metadatas=metadatas
    )

    return collection


# ------------------------------------------------------------------
# Internal Helper: Safe AND Filtering
# ------------------------------------------------------------------

def _filter_records(records, **filters):
    """AND-filter records by metadata."""
    if not filters:
        return records
    filtered = []
    for r in records:
        md = r["metadata"]
        if all(md.get(k) == v for k, v in filters.items()):
            filtered.append(r)
    return filtered


# ------------------------------------------------------------------
# Metadata-only Retrieval (SAFE AND LOGIC)
# ------------------------------------------------------------------

def retrieve_by_metadata(collection, **filters):
    """
    Safe AND filtering on metadata. Returns a list of records.
    Supports zero filters (returns all documents) or multiple filters (AND logic).
    Each record has: {'id', 'document', 'metadata'}
    """
    if filters:
        # Pick first filter for Chroma's where query
        primary_key, primary_value = next(iter(filters.items()))
        raw = collection.get(
            where={primary_key: primary_value},
            include=["documents", "metadatas", "embeddings"],  # valid includes
        )
    else:
        # No filters → retrieve everything
        raw = collection.get(include=["documents", "metadatas", "embeddings"])

    records = [
        {
            "id": raw["ids"][i],
            "document": raw["documents"][i],
            "metadata": raw["metadatas"][i],
            "embedding": raw["embeddings"][i],
        }
        for i in range(len(raw["documents"]))
    ]

    # AND-filtering in Python if multiple filters
    if filters:
        filtered = []
        for r in records:
            if all(r["metadata"].get(k) == v for k, v in filters.items()):
                filtered.append(r)
        return filtered

    return records

# ------------------------------------------------------------------
# RAG-style Retrieval with AND Filters (SAFE)
# ------------------------------------------------------------------

def retrieve_similar_with_filters(
    collection,
    query_embeddings: list | np.ndarray,
    n_results: int = 5,
    category: str | None = None,
    source_context: str | None = None,
    split: str | None = None,
):
    """
    Vector similarity + optional metadata filtering (Chroma-safe).
    Returns one result list per query embedding.

    Args:
        collection: Chroma collection
        query_embeddings: np.ndarray of shape (num_queries, embedding_dim)
                          or (embedding_dim,) for single query
                          or list[list[float]]
        n_results: number of top results to return per query
        category, source_context, split: optional metadata filters
    """

    # Ensure query_embeddings is a list of lists
    if isinstance(query_embeddings, np.ndarray):
        if query_embeddings.ndim == 1:
            query_embeddings = [query_embeddings.tolist()]
        else:
            query_embeddings = query_embeddings.tolist()
    elif isinstance(query_embeddings, list) and isinstance(query_embeddings[0], (float, int)):
        query_embeddings = [query_embeddings]

    # Build metadata filters
    filters = {}
    if split:
        filters["split"] = split
    if category:
        filters["category"] = category
    if source_context:
        filters["source_context"] = source_context

    # Metadata-first retrieval if filters are provided
    if filters:
        candidate_records = retrieve_by_metadata(collection, **filters)

        # If no candidates match, return empty lists for each query
        if not candidate_records:
            return [[] for _ in query_embeddings]

        # Get embeddings for candidates
        candidate_embeddings = [
            collection.get(ids=[r["id"]], include=["embeddings"])["embeddings"][0]
            for r in candidate_records
        ]

        results = []
        for q in query_embeddings:
            dists = np.linalg.norm(np.array(candidate_embeddings) - np.array(q), axis=1)
            top_idx = np.argsort(dists)[:n_results]

            results.append([
                {
                    "id": candidate_records[i]["id"],
                    "document": candidate_records[i]["document"],
                    "metadata": candidate_records[i]["metadata"],
                    "distance": float(dists[i]),
                }
                for i in top_idx
            ])
        return results

    # No metadata filters → direct Chroma query
    raw = collection.query(
        query_embeddings=query_embeddings,
        n_results=n_results,
        include=["documents", "metadatas", "embeddings", "distances"],  # distances included!
    )

    # Format Chroma results consistently
    batched_results = []
    for i in range(len(raw["documents"])):
        batch = []
        for j in range(len(raw["documents"][i])):
            batch.append({
                "id": raw["ids"][i][j],
                "document": raw["documents"][i][j],
                "metadata": raw["metadatas"][i][j],
                "distance": raw["distances"][i][j],
            })
        batched_results.append(batch)

    return batched_results

# ------------------------------------------------------------------
# Convenience Wrappers
# ------------------------------------------------------------------

def retrieve_all(collection):
    """ Return all the documents in the collection. """
    return retrieve_by_metadata(collection)

def retrieve_by_category(collection, category):
    return retrieve_by_metadata(collection, category=category)

def retrieve_by_source_context(collection, source_context):
    return retrieve_by_metadata(collection, source_context=source_context)

def retrieve_by_actionability(collection, actionability_hint):
    return retrieve_by_metadata(collection, actionability_hint=actionability_hint)


# ------------------------------------------------------------------
# Main (Smoke Test)
# ------------------------------------------------------------------

if __name__ == "__main__":
    collection = initialize_db()
    print("Total records after initialization:", collection.count())

    team_docs = retrieve_by_category(collection, "team")
    print("Category=team:", len(team_docs))

    query = "My teammates never communicate deadlines clearly"
    query_emb = encode_texts([query])[0]

    rag_results = retrieve_similar_with_filters(
        collection,
        query_embeddings=query_emb,
        category="team",
        source_context="self_reflection",
        n_results=5,
    )

    print("RAG results:", len(rag_results[0]))
