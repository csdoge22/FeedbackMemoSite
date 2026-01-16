from typing import List
from .dimension_label_proposal import RAGExample


def build_rag_dimension_prompt(
    feedback_text: str,
    evidence: List[RAGExample],
    model_id: str,
) -> str:
    prompt = f"""
You are an annotation assistant ({model_id}).

Label the following feedback along dimensions:
- severity
- urgency
- impact

Return STRICT JSON only.

Feedback:
\"\"\"{feedback_text}\"\"\"

Relevant examples:
"""

    for ex in evidence:
        prompt += (
            f"- Feedback: {ex.text}\n"
            f"  Labels: {ex.labels}\n"
            f"  Priority: {ex.priority}\n"
        )

    prompt += """
Return JSON in this format:
{
  "labels": { "severity": "...", "urgency": "...", "impact": "..." },
  "confidences": { "severity": 0.0, "urgency": 0.0, "impact": 0.0 },
  "rationale": { "severity": "...", "urgency": "...", "impact": "..." },
  "evidence": [],
  "source": "weak_llm",
  "model_id": "<model_id>"
}
"""
    return prompt
