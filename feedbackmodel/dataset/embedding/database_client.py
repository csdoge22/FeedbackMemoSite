# dataset/embedding/database_client.py
import os
import numpy as np
import chromadb
from chromadb.utils import embedding_functions as ef
import logging
from typing import List, Tuple, Any, Optional

from dataset.processing.dataset_loader import load_dataset
from dataset.processing.preprocessing import preprocess_text_series
from dataset.embedding.embedding_cache import EmbeddingCache
from curation.utils.rag_client import CollectionClient
from dataset.embedding.embedding_cache_client import EmbeddingCacheClient

logger = logging.getLogger(__name__)
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
def initialize_collection(client: chromadb.PersistentClient) -> chromadb.api.models.Collection:
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
# Database Initialization
# ------------------------------------------------------------------
def initialize_db(split: str = "train"):
    client = chromadb.PersistentClient(path=BASE_DIR)
    collection = initialize_collection(client)

    embedding_client = EmbeddingCacheClient(split=split)

    texts = embedding_client._texts
    embeddings = embedding_client._embeddings

    df = load_dataset(split)

    metadatas = [
        {
            "split": split,
            "category": str(getattr(row, "category", "")),
            "source_context": str(getattr(row, "source_context", "")),
            "actionability_hint": str(getattr(row, "actionability_hint", "")),
        }
        for row in df.itertuples(index=False)
    ]

    doc_ids = [f"{split}_{i}" for i in range(len(texts))]

    collection.add(
        ids=doc_ids,
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas,
    )

    logger.info(f"[ChromaDB] Added {len(texts)} records for '{split}'")
    return collection


# ------------------------------------------------------------------
# Chroma CollectionClient Implementation
# ------------------------------------------------------------------
class ChromaCollectionClient(CollectionClient):
    """
    Wraps a persistent Chroma collection to conform to CollectionClient.
    Handles:
      - embedding-based retrieval
      - metadata-based filtering
    """

    def __init__(self, collection: Optional[chromadb.api.models.Collection] = None):
        self.collection = collection or self._attach_collection()

    def _attach_collection(self) -> chromadb.api.models.Collection:
        client = chromadb.PersistentClient(path=BASE_DIR)
        return client.get_collection(
            name=COLLECTION_NAME,
            embedding_function=IdentityEmbeddingFunction(),
        )

    # ---------------------
    # Embedding-based retrieval (RAG)
    # ---------------------
    def retrieve(self, query_embedding: List[float], top_k: int = 5) -> List[Tuple[Any, ...]]:
        raw = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "embeddings", "distances"],
        )

        return [
            (doc, {}, meta, float(dist))
            for doc, meta, dist in zip(raw["documents"][0], raw["metadatas"][0], raw["distances"][0])
        ]

    # ---------------------
    # Metadata filtering
    # ---------------------
    def _filter_records(self, records: List[dict], **filters) -> List[dict]:
        if not filters:
            return records
        filtered = []
        for r in records:
            md = r["metadata"]
            if all(md.get(k) == v for k, v in filters.items()):
                filtered.append(r)
        return filtered

    def retrieve_by_metadata(self, **filters) -> List[dict]:
        if filters:
            primary_key, primary_value = next(iter(filters.items()))
            raw = self.collection.get(
                where={primary_key: primary_value},
                include=["documents", "metadatas", "embeddings"],
            )
        else:
            raw = self.collection.get(include=["documents", "metadatas", "embeddings"])

        records = [
            {
                "id": raw["ids"][i],
                "document": raw["documents"][i],
                "metadata": raw["metadatas"][i],
                "embedding": raw["embeddings"][i],
            }
            for i in range(len(raw["documents"]))
        ]

        if filters:
            return self._filter_records(records, **filters)
        return records

    def retrieve_all(self) -> List[dict]:
        return self.retrieve_by_metadata()

    def retrieve_by_category(self, category: str) -> List[dict]:
        return self.retrieve_by_metadata(category=category)

    def retrieve_by_source_context(self, source_context: str) -> List[dict]:
        return self.retrieve_by_metadata(source_context=source_context)

    def retrieve_by_actionability(self, actionability_hint: str) -> List[dict]:
        return self.retrieve_by_metadata(actionability_hint=actionability_hint)

    # ---------------------
    # RAG-style retrieval with optional metadata filters
    # ---------------------
    def retrieve_similar_with_filters(
        self,
        query_embeddings: list | np.ndarray,
        n_results: int = 5,
        category: Optional[str] = None,
        source_context: Optional[str] = None,
        split: Optional[str] = None,
    ) -> list[list[dict]]:
        # Ensure list of lists
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
            candidate_records = self.retrieve_by_metadata(**filters)
            if not candidate_records:
                return [[] for _ in query_embeddings]

            candidate_embeddings = [
                self.collection.get(ids=[r["id"]], include=["embeddings"])["embeddings"][0]
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
        raw = self.collection.query(
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

# ------------------------------------------------------------------
# Optional Smoke Test
# ------------------------------------------------------------------
if __name__ == "__main__":
    collection = initialize_db()
    client = ChromaCollectionClient(collection)

    from curation.utils.rag_client import RAGClient
    rag_client = RAGClient(collection_client=client, top_k=3)

    test_embedding = np.random.rand(384).tolist()  # example embedding
    examples = rag_client.retrieve_similar(test_embedding)
    print("Retrieved examples:", examples)
