import os
import pandas as pd
import pytest

from curation.metadata import (
    ActiveLearningMetadata,
    create_or_load_metadata,
)


def test_create_saves_initial_file(tmp_path):
    p = tmp_path / "meta.tsv"
    df = pd.DataFrame({"feedback_text": ["a", "b", "c"]})

    # create with save_path; factory will attempt an initial save
    meta = create_or_load_metadata(df, save_path=str(p), autosave=False)
    assert os.path.exists(p)

    # mark a row and save explicitly
    batch = meta.query_next_batch(batch_size=2)
    indices = batch.index.tolist()
    meta.mark_as_labeled(indices, ["label1", "label2"])
    meta.save()

    # reload from file and confirm labeled rows persisted
    meta2 = create_or_load_metadata(pd.DataFrame(), save_path=str(p))
    labeled = meta2.get_labeled()
    assert len(labeled) == 2


def test_autosave_on_mark(tmp_path):
    p = tmp_path / "meta_auto.tsv"
    df = pd.DataFrame({"feedback_text": ["x", "y"]})

    meta = create_or_load_metadata(df, save_path=str(p), autosave=True)
    batch = meta.query_next_batch(batch_size=1)
    idx = batch.index.tolist()
    meta.mark_as_labeled(idx, ["done"])

    # file should exist and contain the labeled row
    assert os.path.exists(p)
    reloaded = create_or_load_metadata(pd.DataFrame(), save_path=str(p))
    assert len(reloaded.get_labeled()) == 1


def test_save_without_path_raises():
    df = pd.DataFrame({"feedback_text": ["n"]})
    meta = ActiveLearningMetadata(df)
    with pytest.raises(ValueError):
        meta.save()
