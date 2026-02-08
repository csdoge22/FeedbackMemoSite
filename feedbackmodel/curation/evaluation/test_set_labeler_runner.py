import logging
import pandas as pd
from pathlib import Path
from curation.evaluation.test_set_labeler import TestSetLabeler
from curation.evaluation.test_set_loader import TestSetLoader

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    loader = TestSetLoader(
        test_path="dataset/data/synthetic_feedback_dataset_test.tsv",
        stop_path="dataset/data/synthetic_feedback_dataset_stop.tsv"
    )

    test_df = loader.load_test_set()
    stop_df = loader.load_stop_set()

    labeler = TestSetLabeler()
    test_output = "dataset/data/synthetic_feedback_dataset_test_labeled.tsv"
    stop_output = "dataset/data/synthetic_feedback_dataset_stop_labeled.tsv"

    logger.info("Labeling test set...")
    labeler.label_and_save(test_df, test_output)

    logger.info("Labeling stop set...")
    labeler.label_and_save(stop_df, stop_output)

if __name__ == "__main__":
    main()
