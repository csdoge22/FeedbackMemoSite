# dataset/processing/dataset_loader.py
import os
import pandas as pd

# Base directory where all dataset TSVs are stored
DATA_DIR = os.path.join(os.path.dirname(__file__), "../data")

# Mapping of dataset splits to filenames
DATA_FILES = {
    "full": "synthetic_feedback_dataset.tsv",
    "train": "synthetic_feedback_dataset_train.tsv",
    "test": "synthetic_feedback_dataset_test.tsv",
    "stop": "synthetic_feedback_dataset_stop.tsv",
    "bad": "synthetic_feedback_dataset_bad_rows.tsv"
}

def get_dataset(split: str = "full") -> pd.DataFrame:
    """
    Return the requested dataset split as a pandas DataFrame.

    Args:
        split (str): One of 'full', 'train', 'test', 'stop', 'bad'.

    Returns:
        pd.DataFrame: The requested dataset split.

    Raises:
        ValueError: If split is unknown.
        FileNotFoundError: If the dataset file does not exist.
    """
    if split not in DATA_FILES:
        raise ValueError(f"Unknown split '{split}', must be one of {list(DATA_FILES.keys())}")
    
    path = os.path.abspath(os.path.join(DATA_DIR, DATA_FILES[split]))
    
    if not os.path.exists(path):
        raise FileNotFoundError(f"Dataset file not found at {path}")
    
    return pd.read_csv(path, sep="\t")


def load_dataset(split: str = None) -> pd.DataFrame:
    """
    Unified loader function for consistency across the codebase.

    Args:
        split (str, optional): Dataset split to load. If None, loads full dataset.

    Returns:
        pd.DataFrame: The requested dataset split.
    """
    return get_dataset(split or "full")


def dataset_info(split: str = None) -> None:
    """
    Print basic info about the dataset: shape, columns, first rows.

    Args:
        split (str, optional): Dataset split to inspect. Defaults to full.
    """
    df = load_dataset(split)
    print(f"Dataset split: {split or 'full'}")
    print(f"Shape: {df.shape}")
    print("Columns:", df.columns.tolist())
    print("First 5 rows:\n", df.head())

def get_split_ids(split_name: str = None) -> list[str]:
    """
    Return a list of unique string IDs for a dataset split.
    IDs are in the format 'split_index'.
    
    Args:
        split_name (str, optional): 'train', 'test', 'stop', or None for full dataset.

    Returns:
        list[str]: Unique string IDs for each row.
    """
    df = load_dataset(split_name)
    prefix = split_name if split_name else "full"
    return [f"{prefix}_{i}" for i in range(len(df))]
