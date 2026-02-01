import json
import logging
import lmstudio as lms
import re

logger = logging.getLogger(__name__)

class LLMOracle:
    """
    Drop-in labeling oracle using an LLM.
    Ensures output is parsed as JSON safely.
    """

    def __init__(self, model_name: str = "mistralai/mistral-7b-instruct-v0.3"):
        self.model_name = model_name
        self.model = lms.llm(model_name)

    def label(self, prompt: str) -> str:
        """
        Sends prompt to LLM and returns raw text.
        """
        try:
            result = self.model.respond(prompt)
            return str(result)
        except Exception as e:
            logger.warning(f"LLM call failed: {e}")
            return "{}"  # fallback empty JSON

    def parse_to_proposal(self, raw_output: str) -> dict:
        logger = logging.getLogger(__name__)

        try:
            cleaned = raw_output.strip()

            # Remove code fences
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:].strip().rstrip("```")

            # Ensure property names are quoted
            cleaned = re.sub(r'(\b\w+\b)\s*:', r'"\1":', cleaned)

            parsed = json.loads(cleaned)
            if not isinstance(parsed, dict):
                raise ValueError("Parsed JSON is not a dictionary")
            return parsed
        except Exception as e:
            logger.warning(f"Failed to parse LLM output: {e}\nRaw output: {raw_output}")
            return {
                "severity": "low",
                "urgency": "low",
                "impact": "low"
            }
