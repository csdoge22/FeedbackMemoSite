from curation.utils.priority_utils import compute_priority


def test_compute_priority_basic():
    dims = {"severity": 1.0, "urgency": 0.5}
    p = compute_priority(dims)
    assert isinstance(p, float)
    assert 0.0 <= p <= 1.0


def test_compute_priority_empty():
    assert compute_priority({}) == 0.0
