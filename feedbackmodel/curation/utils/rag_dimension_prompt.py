# curation/utils/rag_dimension_prompt.py
from typing import List
import json
from curation.dimension_label_proposal import RAGExample


def build_rag_dimension_prompt(
    feedback_text: str,
    evidence: List[RAGExample],
    model_id: str,
) -> str:
    """
    Build a RAG-assisted prompt for multi-dimensional labeling.

    Feedback text is JSON-encoded to prevent issues with quotes/newlines.
    """
    safe_feedback_text = json.dumps(feedback_text, ensure_ascii=False)

    prompt = f"""
You are an annotation assistant ({model_id}).

Your task is to label the given feedback along these dimensions:
- severity
- urgency
- impact

Return STRICT JSON only. Do not include explanations or markdown.

Feedback (JSON-encoded string):
{safe_feedback_text}

Relevant examples:
"""

    for ex in evidence:
        example_obj = {
            "feedback": ex.text,
            "labels": ex.labels,
            "priority": ex.priority,
        }
        prompt += json.dumps(example_obj, ensure_ascii=False) + "\n"

    prompt += f"""
Return JSON in exactly this format:
{{
  "labels": {{
    "severity": "low|medium|high",
    "urgency": "low|medium|high",
    "impact": "low|medium|high"
  }},
  "confidences": {{
    "severity": 0.0,
    "urgency": 0.0,
    "impact": 0.0
  }},
  "rationale": {{
    "severity": "",
    "urgency": "",
    "impact": ""
  }},
  "evidence": [],
  "source": "weak_llm",
  "model_id": "{model_id}"
}}

Rules:
- All keys MUST be present.
- If unsure, use empty strings or 0.0 — never omit a field.
- Output MUST be valid JSON.
"""
    return prompt
