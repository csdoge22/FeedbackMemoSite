# curation/utils/rag_client.py
import logging
from typing import List, Optional, Any

from curation.dimension_label_proposal import RAGExample
from dataset.embedding.embedding_cache import EmbeddingCache

logger = logging.getLogger(__name__)


class CollectionClient:
    """
    Abstract base class for a collection/database client.
    Subclasses must implement retrieve for a single query embedding.
    """

    def retrieve(self, query_embedding: List[float], top_k: int) -> List[Any]:
        raise NotImplementedError


class RAGClient:
    """
    RAG client adapter that converts raw collection results into RAGExample objects.
    Supports batching multiple query embeddings and can optionally use cached embeddings.

    Args:
        collection_client: Optional subclass of CollectionClient.
        embedding_cache: Optional EmbeddingCache instance for local retrieval.
        top_k: Number of nearest neighbors to retrieve per query embedding.
    """

    def __init__(
        self,
        collection_client: Optional[CollectionClient] = None,
        embedding_cache: Optional[EmbeddingCache] = None,
        top_k: int = 5
    ):
        self.collection_client = collection_client
        self.embedding_cache = embedding_cache or EmbeddingCache()
        self.top_k = top_k
        logger.info(f"RAGClient initialized with top_k={top_k}")

    def retrieve_similar(
        self,
        query_embeddings: List[List[float]],
        category: Optional[str] = None,
        source_context: Optional[str] = None,
        split: Optional[str] = None
    ) -> List[List[RAGExample]]:
        """
        Retrieve top-k RAG examples for each query embedding.
        First tries the embedding cache, then optionally falls back to collection client.

        Returns:
            List of lists of RAGExample objects.
        """
        # Ensure batch format
        if isinstance(query_embeddings[0], (float, int)):
            query_embeddings = [query_embeddings]

        all_examples: List[List[RAGExample]] = []

        for emb in query_embeddings:
            # -----------------------------
            # Try local retrieval from EmbeddingCache
            # -----------------------------
            retrieved = []
            if self.embedding_cache is not None and split is not None:
                retrieved_texts, distances = self.embedding_cache.retrieve_similar(
                    emb, split=split, top_k=self.top_k
                )
                for text, dist in zip(retrieved_texts, distances):
                    retrieved.append(
                        RAGExample(
                            text=text,
                            labels={},
                            priority=1.0 if dist is None else 1.0 / (1.0 + dist),
                            metadata={"split": split},
                            distance=dist,
                        )
                    )

            # -----------------------------
            # Fallback: external collection client
            # -----------------------------
            if self.collection_client is not None:
                if hasattr(self.collection_client, "retrieve_similar_with_filters"):
                    raw_results = self.collection_client.retrieve_similar_with_filters(
                        query_embeddings=[emb],
                        n_results=self.top_k,
                        category=category,
                        source_context=source_context,
                        split=split
                    )[0]
                else:
                    raw_results = self.collection_client.retrieve(query_embedding=emb, top_k=self.top_k)

                for r in raw_results:
                    if not isinstance(r, (list, tuple, dict)):
                        continue

                    if isinstance(r, dict):
                        text = r.get("document", "")
                        metadata_ = r.get("metadata", {})
                        distance = r.get("distance")
                    else:  # list/tuple fallback
                        text = r[0]
                        metadata_ = r[2] if len(r) > 2 and isinstance(r[2], dict) else {}
                        distance = r[3] if len(r) > 3 and isinstance(r[3], (int, float)) else None

                    retrieved.append(
                        RAGExample(
                            text=text,
                            labels={},
                            priority=1.0 if distance is None else 1.0 / (1.0 + distance),
                            metadata=metadata_,
                            distance=distance
                        )
                    )

            # Keep only top-k
            retrieved = sorted(retrieved, key=lambda x: x.priority, reverse=True)[:self.top_k]
            all_examples.append(retrieved)
            logger.info(f"Retrieved {len(retrieved)} examples for one query embedding")

        return all_examples


# -----------------------------
# Optional Dummy Client
# -----------------------------
class DummyCollectionClient(CollectionClient):
    """Dummy client returning placeholder results for testing."""

    def retrieve(self, query_embedding: List[float], top_k: int) -> List[Any]:
        return [("Sample feedback text", {}, {}, 0.0) for _ in range(top_k)]
