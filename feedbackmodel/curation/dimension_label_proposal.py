from dataclasses import dataclass
from typing import Dict, List, Any, Optional


@dataclass
class LabelValue:
    value: str


@dataclass
class RAGExample:
    text: str
    labels: Dict[str, str]
    priority: float
    metadata: Dict[str, Any]
    distance: Optional[float] = None

@dataclass
class DimensionLabelProposal:
    labels: Dict[str, LabelValue]
    confidences: Dict[str, float]
    rationale: Dict[str, str]
    evidence: List[RAGExample]
    source: str
    model_id: str
