# dataset/analysis/plot_dataset_utils.py
import os
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from dataset.processing.dataset_loader import load_dataset

PLOTS_DIR = os.path.join(os.path.dirname(__file__), "plots")
os.makedirs(PLOTS_DIR, exist_ok=True)

def plot_distribution(
    df: pd.DataFrame,
    column: str,
    plot_filename: str,
    title: str = None,
    train_fraction: float = 0.8
) -> tuple[pd.Series, pd.Series]:
    """
    Generic function to plot distribution of a column and compute train split sizes.

    Args:
        df (pd.DataFrame): Dataset.
        column (str): Column name to analyze.
        plot_filename (str): Filename to save the plot.
        title (str, optional): Plot title.
        train_fraction (float): Fraction of data to allocate for training.

    Returns:
        tuple[pd.Series, pd.Series]: (value counts, train split counts)
    """
    if column not in df.columns:
        raise ValueError(f"Column '{column}' not found in dataset.")

    counts = df[column].value_counts()
    
    # Plot
    plt.figure(figsize=(20, 7))
    plt.bar(counts.index, counts.values)
    plt.title(title or f"{column} Distribution")
    plt.xlabel(column)
    plt.ylabel("Count")
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, plot_filename))
    plt.close()
    
    # Compute train split sizes
    train_sizes = pd.Series(np.ceil(counts * train_fraction), dtype=int)
    
    print(f"Distribution for '{column}':\n{counts}")
    print(f"Train split (fraction={train_fraction}):\n{train_sizes}")
    
    return counts, train_sizes


# Specific helpers for convenience
def source_context_distribution(split: str = None):
    df = load_dataset(split)
    return plot_distribution(df, "source_context", "distribution1.png", title="Source Context Distribution")


def category_distribution(split: str = None):
    df = load_dataset(split)
    return plot_distribution(df, "category", "distribution2.png", title="Category Distribution")


def actionability_hint_distribution(split: str = None):
    df = load_dataset(split)
    return plot_distribution(df, "actionability_hint", "distribution3.png", title="Actionability Hint Distribution")


if __name__ == "__main__":
    # Example usage
    source_context_distribution()
    category_distribution()
    actionability_hint_distribution()
