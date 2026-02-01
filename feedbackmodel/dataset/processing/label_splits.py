import os
import pandas as pd

def label_dataset_split(input_path: str, output_path: str, label_fn):
    """
    Apply ground-truth labels to a fixed dataset split (test or stop).
    `label_fn` acts as the labeling oracle.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input path {input_path} does not exist.")

    dataset = pd.read_csv(input_path, sep="\t")

    # Initialize label columns
    for col in ["severity", "urgency", "impact"]:
        if col not in dataset.columns:
            dataset[col] = pd.NA

    for i, row in dataset.iterrows():
        text = row["feedback_text"]

        labels = label_fn(text)  # <-- SINGLE source of truth

        dataset.at[i, "severity"] = labels["severity"]
        dataset.at[i, "urgency"] = labels["urgency"]
        dataset.at[i, "impact"] = labels["impact"]

    dataset.to_csv(output_path, sep="\t", index=False)

