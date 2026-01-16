from typing import List, Dict, Any
import json

from dataset.embedding.embedding_generator import encode_texts
from .metadata import ActiveLearningMetadata
from .rag_client import RAGClient
from .rag_dimension_prompt import build_rag_dimension_prompt
from .dimension_label_proposal import DimensionLabelProposal, LabelValue, RAGExample


class HumanLabeling:
    def __init__(self, metadata: ActiveLearningMetadata, rag_client: RAGClient, llm_call_fn):
        self.metadata = metadata
        self.rag_client = rag_client
        self.llm_call_fn = llm_call_fn

    def label_batch(self, feedback_indices: List[int], model_id: str):
        proposals = []

        for idx in feedback_indices:
            record = self.metadata.records[idx]
            feedback_text = record["text"]

            # 1️⃣ Embed the feedback text
            embedding = encode_texts([feedback_text])[0]

            # 2️⃣ Retrieve similar examples from RAG
            retrieved = self.rag_client.retrieve_similar(embedding)

            # 2a️⃣ Include seed evidence if present
            if "seed_proposal" in record and record["seed_proposal"]:
                retrieved = record["seed_proposal"].evidence + retrieved

            # 3️⃣ Build prompt for the LLM
            prompt = build_rag_dimension_prompt(feedback_text, retrieved, model_id)

            # 4️⃣ Call the LLM and parse JSON
            raw_output = self.llm_call_fn(prompt)
            try:
                proposal_json = json.loads(raw_output)
            except Exception as e:
                print(f"[Warning] LLM output could not be parsed for idx {idx}: {e}")
                continue

            # 5️⃣ Guardrail: Validate evidence
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
                metadata = ex.get("metadata", {})
                distance = ex.get("distance")
                evidence.append(
                    RAGExample(
                        text=text,
                        labels=labels,
                        priority=priority,
                        metadata=metadata,
                        distance=distance,
                    )
                )

            # 6️⃣ Guardrail: Validate main proposal fields
            labels_dict = proposal_json.get("labels", {})
            confidences_dict = proposal_json.get("confidences", {})
            rationale_dict = proposal_json.get("rationale", {})
            source = proposal_json.get("source", "unknown")
            proposal_model_id = proposal_json.get("model_id", model_id)

            proposal = DimensionLabelProposal(
                labels={k: LabelValue(v) for k, v in labels_dict.items()},
                confidences=confidences_dict,
                rationale=rationale_dict,
                evidence=evidence,
                source=source,
                model_id=proposal_model_id,
            )

            proposals.append(proposal)

        # 7️⃣ Mark items as labeled
        self.metadata.mark_as_labeled(feedback_indices, proposals)
