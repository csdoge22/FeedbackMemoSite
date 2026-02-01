# dataset/processing/load_splits.py

from pathlib import Path
import pandas as pd

DATA_DIR = Path("dataset/data")

def load_split(split: str) -> pd.DataFrame:
    """
    Load a dataset split.

    Args:
        split: one of {"train", "test", "stop", "test_labeled", "stop_labeled"}

    Returns:
        pandas.DataFrame
    """
    path = DATA_DIR / f"synthetic_feedback_dataset_{split}.tsv"
    if not path.exists():
        raise FileNotFoundError(f"Split not found: {path}")

    return pd.read_csv(path, sep="\t")
