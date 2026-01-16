import numpy as np
import pandas as pd

from curation.metadata import create_or_load_metadata
from curation.model import run_active_learning_loop


def test_map_and_query_strategies(tmp_path):
    df = pd.DataFrame({"feedback_text": ["a", "b", "c", "d", "e"]}, index=[0, 1, 2, 3, 4])
    meta = create_or_load_metadata(df, seed_indices=[0])

    # label the seed so it will be excluded from queries
    meta.mark_as_labeled([0], ["seed"])

    # probs aligned to full dataset (5 x 3)
    probs_all = np.array([
        [0.9, 0.05, 0.05],
        [0.4, 0.3, 0.3],
        [0.33, 0.33, 0.34],
        [0.6, 0.2, 0.2],
        [0.2, 0.4, 0.4],
    ])

    # map to unlabeled ordering (should exclude index 0)
    probs_unl = meta.map_to_unlabeled(probs_all)
    assert probs_unl.shape[0] == 4

    batch = meta.query_next_batch(batch_size=2, strategy="least_confidence", probs=probs_unl)
    # at least one and at most batch_size items should be returned
    assert 1 <= len(batch) <= 2
    assert 0 not in batch.index

    # test with pandas Series mapping
    rag_conf_series = pd.Series([0.9, 0.2, 0.3, 0.8, 0.4], index=df.index)
    rag_unl = meta.map_to_unlabeled(rag_conf_series)
    assert len(rag_unl) == 4


def test_run_active_learning_loop_simulation(tmp_path):
    texts = [f"sample {i}" for i in range(6)]
    df = pd.DataFrame({"feedback_text": texts}, index=list(range(6)))
    outputs = {"df": df}

    # seeds at 0 and 1
    meta = create_or_load_metadata(df, seed_indices=[0, 1])

    # simulated RAG labels for all rows
    rag = {i: ("A" if i % 2 == 0 else "B") for i in df.index}

    clf, final_meta = run_active_learning_loop(
        outputs,
        meta,
        human_label_fn=None,
        rag_labels=rag,
        auto_label_pool=False,
        n_rounds=2,
        batch_size=2,
        strategy="least_confidence",
        calibrate=False,
    )

    # classifier should be returned and metadata should have labeled items (at least the seeds)
    assert hasattr(clf, "predict_proba")
    assert len(final_meta.get_labeled()) >= 2
