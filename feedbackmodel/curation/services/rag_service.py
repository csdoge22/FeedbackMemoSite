# curation/services/rag_service.py
import logging
from typing import List, Optional, Protocol, Any

from curation.dimension_label_proposal import RAGExample

logger = logging.getLogger(__name__)


class CollectionClient(Protocol):
    """
    Protocol for dependency injection of a collection/database client.
    """
    def retrieve(self, query_embedding: List[float], top_k: int) -> List[Any]:
        ...


class RAGService:
    """
    Service layer for RAG-assisted retrieval.

    - Accepts a collection client.
    - Returns structured RAGExample objects.
    """

    def __init__(self, collection_client: CollectionClient, top_k: int = 5):
        self.collection_client = collection_client
        self.top_k = top_k
        logger.info(f"RAGService initialized with top_k={top_k}")

    def retrieve_similar(self, query_embedding: List[float]) -> List[RAGExample]:
        results = self.collection_client.retrieve(query_embedding=query_embedding, top_k=self.top_k)
        examples: List[RAGExample] = []

        for r in results:
            if not isinstance(r, (list, tuple)):
                raise TypeError(f"Unexpected RAG result type: {type(r)}")

            text = r[0]
            metadata_ = r[2] if len(r) > 2 and isinstance(r[2], dict) else {}
            distance: Optional[float] = None
            if len(r) > 3:
                if isinstance(r[3], (int, float)):
                    distance = float(r[3])
                elif isinstance(r[3], dict):
                    distance = r[3].get("distance")

            examples.append(
                RAGExample(
                    text=text,
                    labels={},
                    priority=1.0 if distance is None else 1.0 / (1.0 + distance),
                    metadata=metadata_,
                    distance=distance,
                )
            )

        logger.info(f"Retrieved {len(examples)} examples from RAGService")
        return examples
