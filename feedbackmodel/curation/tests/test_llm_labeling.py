import curation.labeling.llm_labeling as llm_labeling


def test_llm_labeling_module_importable():
    # Ensures module loads and dependencies are satisfied
    assert llm_labeling is not None


def test_llm_labeling_has_callable_components():
    callables = [
        name for name in dir(llm_labeling)
        if not name.startswith("_")
        and callable(getattr(llm_labeling, name))
    ]

    assert len(callables) > 0
