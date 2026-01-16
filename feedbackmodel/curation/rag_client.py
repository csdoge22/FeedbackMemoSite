from dataset.embedding.database_client import (
    get_collection,
    retrieve_similar_with_filters,
)
from .dimension_label_proposal import RAGExample


class RAGClient:
    def __init__(self, collection=None, top_k: int = 5):
        self.collection = collection or get_collection()
        self.top_k = top_k

    def retrieve_similar(self, query_embedding):
        results = retrieve_similar_with_filters(
            collection=self.collection,
            query_embeddings=query_embedding.tolist(),
            n_results=self.top_k,
        )

        examples = []

        for r in results:
            if not isinstance(r, (list, tuple)):
                raise TypeError(f"Unexpected RAG result type: {type(r)}")

            text = r[0]
            metadata = r[2] if len(r) > 2 and isinstance(r[2], dict) else {}

            # Distance may be nested in a dict
            distance = None
            if len(r) > 3:
                if isinstance(r[3], (int, float)):
                    distance = float(r[3])
                elif isinstance(r[3], dict):
                    distance = r[3].get("distance")

            examples.append(
                RAGExample(
                    text=text,
                    labels={},                     # retrieved examples are unlabeled
                    priority=1.0 if distance is None else 1.0 / (1.0 + distance),
                    metadata=metadata,
                    distance=distance,
                )
            )

        return examples
