from curation.seeds.seed_factory import default_seed_proposal
from curation.dimension_label_proposal import DimensionLabelProposal


def test_default_seed_proposal_returns_proposal():
    proposal = default_seed_proposal(0, "Seed feedback")

    assert isinstance(proposal, DimensionLabelProposal)
    assert proposal.source == "seed"
    assert proposal.labels == {}
