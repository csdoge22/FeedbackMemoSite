from curation.query.query_strategies import least_confidence_sampling


def test_least_confidence_sampling_basic():
    records = [
        {"labeled": False, "confidences": {"model": 0.9}},
        {"labeled": False, "confidences": {"model": 0.1}},
        {"labeled": False, "confidences": {"model": 0.5}},
    ]

    selected = least_confidence_sampling(records, n=2)
    assert selected == [1, 2]


def test_least_confidence_sampling_ignores_labeled():
    records = [
        {"labeled": True, "confidences": {"model": 0.0}},
        {"labeled": False, "confidences": {"model": 0.2}},
    ]

    selected = least_confidence_sampling(records, n=1)
    assert selected == [1]
