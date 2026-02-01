# curation/labeling/human_labeling.py

import logging
import json
from typing import List, Optional

from curation.metadata.metadata import ActiveLearningMetadata
from curation.dimension_label_proposal import DimensionLabelProposal, LabelValue, RAGExample
from curation.utils.rag_client import RAGClient
from curation.utils.rag_dimension_prompt import build_rag_dimension_prompt
from dataset.embedding.embedding_cache import EmbeddingCache

logger = logging.getLogger(__name__)


class HumanLabeling:
    """
    Handles human-in-the-loop labeling with optional RAG assistance.
    Uses a shared EmbeddingCache for consistent embeddings across pipeline.
    """

    def __init__(
        self,
        metadata: ActiveLearningMetadata,
        rag_client: RAGClient,
        llm_call_fn,
        embedding_cache: Optional[EmbeddingCache] = None
    ):
        self.metadata = metadata
        self.rag_client = rag_client
        self.llm_call_fn = llm_call_fn
        # Use provided cache or create a new one
        self.embedding_cache = embedding_cache or EmbeddingCache()

    def label_batch(self, feedback_indices: List[int], model_id: str):
        proposals = []

        for idx in feedback_indices:
            record = self.metadata.records[idx]
            feedback_text = record["text"]

            # -----------------------------
            # Generate embedding using cache
            # -----------------------------
            embedding = self.embedding_cache.encode_texts([feedback_text])[0]

            # -----------------------------
            # Retrieve RAG examples
            # -----------------------------
            retrieved = self.rag_client.retrieve_similar([embedding])[0]

            if record.get("seed_proposal"):
                retrieved = record["seed_proposal"].evidence + retrieved

            # -----------------------------
            # Build prompt and call LLM
            # -----------------------------
            prompt = build_rag_dimension_prompt(feedback_text, retrieved, model_id)
            raw_output = self.llm_call_fn(prompt)

            # -----------------------------
            # Parse JSON output
            # -----------------------------
            try:
                proposal_json = json.loads(raw_output)
            except Exception as e:
                logger.warning(f"LLM output could not be parsed for idx {idx}: {e}")
                continue

            # -----------------------------
            # Parse evidence
            # -----------------------------
            evidence: List[RAGExample] = []
            for ex in proposal_json.get("evidence", []):
                if not isinstance(ex, dict):
                    continue
                text = ex.get("text")
                if not text:
                    continue
                labels = ex.get("labels", {})
                if not isinstance(labels, dict):
                    labels = {}
                priority = ex.get("priority", 1.0)
                metadata_ = ex.get("metadata", {})
                distance = ex.get("distance")
                evidence.append(
                    RAGExample(
                        text=text,
                        labels=labels,
                        priority=priority,
                        metadata=metadata_,
                        distance=distance,
                    )
                )

            # -----------------------------
            # Parse labels and metadata
            # -----------------------------
            labels_dict = proposal_json.get("labels", {})
            confidences_dict = proposal_json.get("confidences", {})
            rationale_dict = proposal_json.get("rationale", {})
            source = proposal_json.get("source", "unknown")
            proposal_model_id = proposal_json.get("model_id", model_id)

            # -----------------------------
            # Build DimensionLabelProposal
            # -----------------------------
            proposal = DimensionLabelProposal(
                labels={k: LabelValue(v) for k, v in labels_dict.items()},
                confidences=confidences_dict,
                rationale=rationale_dict,
                evidence=evidence,
                source=source,
                model_id=proposal_model_id,
            )

            logger.info(f"Proposal for idx {idx}: labels={labels_dict}, source={source}")
            proposals.append(proposal)

        # -----------------------------
        # Mark records as labeled
        # -----------------------------
        self.metadata.mark_as_labeled(feedback_indices, proposals)
        logger.info(f"Marked {len(proposals)} items as labeled")
