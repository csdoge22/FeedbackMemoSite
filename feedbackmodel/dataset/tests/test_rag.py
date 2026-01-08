# tests/test_rag.py
import pytest
import numpy as np

from dataset.embedding.database_client import (
    initialize_db,
    retrieve_by_category,
    retrieve_by_metadata,
    retrieve_similar_with_filters,
)
from dataset.embedding.embedding_generator import encode_texts


@pytest.fixture(scope="module")
def collection():
    """Initialize the Chroma collection once per test module."""
    return initialize_db()


def test_retrieve_by_category_returns_only_category(collection):
    results = retrieve_by_category(collection, "team")
    assert len(results) > 0, "No documents found for category 'team'."
    for r in results:
        assert r["metadata"]["category"] == "team"


def test_retrieve_by_metadata_no_results(collection):
    results = retrieve_by_metadata(collection, category="non_existent_category")
    assert results == [], "Expected empty list for nonexistent metadata filter."


def test_similarity_search_returns_semantically_related_docs(collection):
    query = "I need to improve communication with my team"
    query_emb = encode_texts([query])  # <- returns shape (1, 384)

    results = retrieve_similar_with_filters(
        collection,
        query_embeddings=query_emb,  # pass the full array, not just [0]
        n_results=5,
        category="team",
    )

    assert len(results) == 1
    batch = results[0]
    assert len(batch) > 0
    joined_text = " ".join(item["document"].lower() for item in batch)
    assert "team" in joined_text or "communication" in joined_text


def test_retrieval_shapes_are_consistent(collection):
    results = retrieve_by_category(collection, "team")
    assert all("id" in r and "document" in r and "metadata" in r for r in results)


def test_rag_is_deterministic(collection):
    query = "How can I reflect on team collaboration?"
    query_emb = encode_texts([query])[0]

    r1 = retrieve_similar_with_filters(
        collection,
        query_embeddings=query_emb,
        category="team",
        n_results=3,
    )
    r2 = retrieve_similar_with_filters(
        collection,
        query_embeddings=query_emb,
        category="team",
        n_results=3,
    )

    assert r1 == r2, "RAG results should be deterministic for the same query."


def test_rag_returns_empty_for_unmatched_filters(collection):
    query = "Any random query"
    query_emb = encode_texts([query])  # wrap in list

    results = retrieve_similar_with_filters(
        collection,
        query_embeddings=query_emb,
        category="non_existent_category",
        n_results=3,
    )
    assert results == [[]], "RAG should return empty results for unmatched filters."
