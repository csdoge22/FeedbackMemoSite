import os
import numpy as np
import chromadb
from chromadb.utils import embedding_functions as ef

from dataset.processing.dataset_loader import load_dataset
from dataset.embedding.embedding_generator import encode_dataset_split
from dataset.processing.preprocessing import preprocess_text_series

# ------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "chroma"))
COLLECTION_NAME = "feedback_priority_rag"

# ------------------------------------------------------------------
# Identity Embedding Function for Chroma
# ------------------------------------------------------------------
class IdentityEmbeddingFunction(ef.EmbeddingFunction):
    """Prevents Chroma from recomputing embeddings (assumes precomputed)."""
    def __init__(self):
        super().__init__()
    def __call__(self, input):
        return input

# ------------------------------------------------------------------
# Initialize Collection
# ------------------------------------------------------------------
def initialize_collection(client: chromadb.PersistentClient):
    os.makedirs(BASE_DIR, exist_ok=True)

    existing = [c.name for c in client.list_collections()]
    if COLLECTION_NAME in existing:
        client.delete_collection(name=COLLECTION_NAME)
        print(f"Deleted existing collection '{COLLECTION_NAME}'")

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=IdentityEmbeddingFunction(),
    )
    return collection

# ------------------------------------------------------------------
# Initialize Database with Preprocessing
# ------------------------------------------------------------------
def initialize_db(split="train") -> chromadb.api.models.Collection:
    """
    Load dataset, preprocess text, generate/load embeddings, and populate Chroma DB.
    """
    client = chromadb.PersistentClient(path=BASE_DIR)
    collection = initialize_collection(client)

    # Load dataset
    df = load_dataset(split)

    # -------------------------
    # Preprocess text BEFORE embedding
    # -------------------------
    df["feedback_text"] = preprocess_text_series(df["feedback_text"])

    # Encode embeddings (cached)
    ids, embeddings = encode_dataset_split(split)

    # Build metadata
    metadatas = []
    for row in df.itertuples(index=False):
        metadatas.append({
            "split": split,
            "category": str(getattr(row, "category", "")),
            "source_context": str(getattr(row, "source_context", "")),
            "actionability_hint": str(getattr(row, "actionability_hint", "")),
        })

    # Prepare document IDs
    doc_ids = [f"{split}_{fid}" for fid in df["feedback_id"]]

    # Add to Chroma collection
    collection.add(
        ids=doc_ids,
        documents=df["feedback_text"].tolist(),
        embeddings=embeddings,
        metadatas=metadatas
    )

    print(f"Added {len(df)} documents to collection '{COLLECTION_NAME}'")
    return collection

# ------------------------------------------------------------------
# Retrieval Utilities (unchanged, just safe metadata filtering)
# ------------------------------------------------------------------
def _filter_records(records, **filters):
    if not filters:
        return records
    filtered = []
    for r in records:
        md = r["metadata"]
        if all(md.get(k) == v for k, v in filters.items()):
            filtered.append(r)
    return filtered

def retrieve_by_metadata(collection, **filters):
    if filters:
        primary_key, primary_value = next(iter(filters.items()))
        raw = collection.get(
            where={primary_key: primary_value},
            include=["documents", "metadatas", "embeddings"],
        )
    else:
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

    # Apply AND filtering in Python
    if filters:
        return _filter_records(records, **filters)
    return records

def retrieve_all(collection):
    return retrieve_by_metadata(collection)

def retrieve_by_category(collection, category):
    return retrieve_by_metadata(collection, category=category)

def retrieve_by_source_context(collection, source_context):
    return retrieve_by_metadata(collection, source_context=source_context)

def retrieve_by_actionability(collection, actionability_hint):
    return retrieve_by_metadata(collection, actionability_hint=actionability_hint)

# ------------------------------------------------------------------
# RAG-style Retrieval with Metadata Filters
# ------------------------------------------------------------------
def retrieve_similar_with_filters(
    collection,
    query_embeddings: list | np.ndarray,
    n_results: int = 5,
    category: str | None = None,
    source_context: str | None = None,
    split: str | None = None,
):
    # Ensure query_embeddings is list of lists
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

    # Metadata-first retrieval
    if filters:
        candidate_records = retrieve_by_metadata(collection, **filters)
        if not candidate_records:
            return [[] for _ in query_embeddings]

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

    # No metadata → direct Chroma query
    raw = collection.query(
        query_embeddings=query_embeddings,
        n_results=n_results,
        include=["documents", "metadatas", "embeddings", "distances"],
    )

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

def get_collection() -> chromadb.api.models.Collection:
    """
    Attach to an existing persistent Chroma collection.
    Does NOT modify or recreate the DB.
    """
    client = chromadb.PersistentClient(path=BASE_DIR)
    return client.get_collection(
        name=COLLECTION_NAME,
        embedding_function=IdentityEmbeddingFunction(),
    )

# ------------------------------------------------------------------
# Smoke Test
# ------------------------------------------------------------------
if __name__ == "__main__":
    collection = initialize_db()
    print("Total records:", collection.count())

    team_docs = retrieve_by_category(collection, "team")
    print("Category=team:", len(team_docs))
