from typing import List
from curation.dimension_label_proposal import DimensionLabelProposal, LabelValue

# Define the dimensions you care about
DEFAULT_DIMENSIONS = ["severity", "urgency", "impact"]

# Allowed labels per dimension
LABEL_CHOICES = {
    "severity": ["low", "medium", "high"],
    "urgency": ["low", "medium", "high"],
    "impact": ["medium", "high"],  # low is not used for impact
}

def seeded_seed_proposal(idx: int, text: str, dimensions: List[str] = None) -> DimensionLabelProposal:
    """
    Return a seed proposal for a feedback item with initial labels for all dimensions.
    Labels are assigned in a round-robin fashion across seeds to ensure diversity.
    """
    dimensions = dimensions or DEFAULT_DIMENSIONS

    labels = {}
    for dim in dimensions:
        choices = LABEL_CHOICES[dim]
        # Round-robin assignment based on index to inject diversity
        selected_label = choices[idx % len(choices)]
        labels[dim] = LabelValue(selected_label)

    return DimensionLabelProposal(
        labels=labels,
        confidences={dim: 1.0 for dim in dimensions},  # max confidence for seeds
        rationale={dim: "initial seed" for dim in dimensions},
        evidence=[],
        source="seed",
        model_id="seed"
    )

class SeedFactory:
    """Callable factory that produces seed proposals with initial labels."""
    def __init__(self, dimensions: List[str] = None):
        self.dimensions = dimensions or DEFAULT_DIMENSIONS

    def __call__(self, idx: int, text: str):
        return seeded_seed_proposal(idx, text, self.dimensions)
