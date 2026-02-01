import curation.evaluation.evaluation as evaluation


def test_evaluation_module_has_public_callables():
    public_callables = [
        name for name in dir(evaluation)
        if not name.startswith("_")
        and callable(getattr(evaluation, name))
    ]

    # At least one evaluation-related callable should exist
    assert len(public_callables) > 0
