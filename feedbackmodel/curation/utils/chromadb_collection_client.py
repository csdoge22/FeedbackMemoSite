# curation/utils/chromadb_collection_client.py
from typing import List, Tuple, Any
import numpy as np
import chromadb
from curation.utils.rag_client import CollectionClient
from curation.utils.rag_client import logger

BASE_DIR = "data/chroma"
COLLECTION_NAME = "feedback_priority_rag"


class ChromaCollectionClient(CollectionClient):
    """
    Concrete CollectionClient using ChromaDB as the backend.
    Implements the abstract `retrieve` method.
    """

    def __init__(self, collection: chromadb.api.models.Collection):
        self.collection = collection

    def retrieve(self, query_embedding: List[float], top_k: int) -> List[Tuple[Any, ...]]:
        """
        Retrieve top-k similar records from ChromaDB for a single query embedding.
        Returns a list of tuples: (document_text, metadata_dict, optional_metadata, distance)
        """
        if not isinstance(query_embedding, list):
            query_embedding = query_embedding.tolist()

        raw = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )

        results = []
        for i in range(len(raw["documents"][0])):
            results.append((
                raw["documents"][0][i],
                raw["metadatas"][0][i],
                {},  # placeholder for optional metadata slot
                float(raw["distances"][0][i])
            ))

        logger.info(f"ChromaCollectionClient: retrieved {len(results)} items")
        return results


# -----------------------------
# Utility function to attach to existing collection
# -----------------------------
def get_chroma_client() -> ChromaCollectionClient:
    client = chromadb.PersistentClient(path=BASE_DIR)
    collection = client.get_collection(name=COLLECTION_NAME)
    return ChromaCollectionClient(collection)
