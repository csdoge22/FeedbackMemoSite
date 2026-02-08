import pandas as pd
from typing import List, Dict

class TestSetLoader:
    def __init__(self, test_path: str, stop_path: str):
        self.test_path = test_path
        self.stop_path = stop_path

    def load_test_set(self) -> pd.DataFrame:
        return pd.read_csv(self.test_path, sep="\t")

    def load_stop_set(self) -> pd.DataFrame:
        return pd.read_csv(self.stop_path, sep="\t")

    def get_texts_and_labels(self, df: pd.DataFrame, label_cols: List[str]) -> Dict[str, list]:
        """
        Returns dict with 'texts' and 'labels' for each dimension
        """
        if "feedback_text" not in df.columns:
            raise ValueError("DataFrame must have a 'feedback_text' column.")

        texts = df["feedback_text"].tolist()
        labels = {dim: df[dim].tolist() for dim in label_cols if dim in df.columns}
        return {"texts": texts, "labels": labels}
