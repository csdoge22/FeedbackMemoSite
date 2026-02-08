# curation/utils/metrics.py
import json
import logging
from pathlib import Path
from typing import Dict, Any


class ALMetricsTracker:
    """
    Logger for active learning metrics.
    Writes JSON logs to a file.
    """

    def __init__(self, log_path: Path):
        self.logger = logging.getLogger("active_learning.metrics")
        self.logger.setLevel(logging.INFO)

        handler = logging.FileHandler(log_path, mode="w")
        handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))

        self.logger.addHandler(handler)
        self.logger.propagate = False

    def log(self, metrics: Dict[str, Any]) -> None:
        self.logger.info(json.dumps(metrics))
