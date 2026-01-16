import json
import lmstudio as lms

from dataset.analysis.dataset_clustering import run_clustering_pipeline
from curation.metadata import ActiveLearningMetadata
from curation.human_labeling import HumanLabeling
from curation.query_strategies import least_confidence_sampling
from curation.rag_client import RAGClient
from curation.dimension_label_proposal import DimensionLabelProposal, LabelValue

BATCH_SIZE = 5
MODEL_ID = "weak_llm_v1"


def llm_call_fn(prompt: str) -> str:
    model = lms.llm("mistralai/mistral-7b-instruct-v0.3")
    result = model.respond(prompt)

    # LM Studio 1.5.0 FIX
    return str(result)


def seed_proposal_factory(idx, text):
    dims = ["severity", "urgency", "impact"]
    return DimensionLabelProposal(
        labels={d: LabelValue("medium") for d in dims},
        confidences={d: 0.8 for d in dims},
        rationale={d: "seed" for d in dims},
        evidence=[],
        source="seed",
        model_id="seed_v1",
    )


def main():
    outputs = run_clustering_pipeline(split="train", initial_seed_count=50, plot=False)
    df = outputs["df"]
    seed_indices = outputs["seed_indices"]

    metadata = ActiveLearningMetadata(
        feedback_texts=df["feedback_text"].tolist(),
        seed_indices=seed_indices,
        seed_proposal_factory=seed_proposal_factory,
    )

    labeling = HumanLabeling(metadata, RAGClient(), llm_call_fn)

    while not metadata.done():
        indices = least_confidence_sampling(metadata.records, n=BATCH_SIZE)
        if not indices:
            break

        print("[Labeling]", indices)
        labeling.label_batch(indices, MODEL_ID)

    metadata.save("metadata.json")
    print("[Done]")


if __name__ == "__main__":
    main()
