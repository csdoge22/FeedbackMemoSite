import logging
import pandas as pd
from pathlib import Path
from ruamel.yaml import YAML
from curation.labeling.llm_labeling import LLMOracle

logger = logging.getLogger(__name__)

MAX_RETRIES = 3

class TestSetLabeler:
    def __init__(
        self,
        prompt_yaml_path: str = None,
        model_name: str = "mistralai/mistral-7b-instruct-v0.3"
    ):
        # Load YAML configuration
        if prompt_yaml_path is None:
            prompt_yaml_path = Path(__file__).parent.parent / "prompts" / "test_set_labeling.yaml"
        self.yaml_path = Path(prompt_yaml_path)
        yaml = YAML(typ="safe")
        with open(self.yaml_path, "r") as f:
            self.config = yaml.load(f)

        # Extract text placeholder
        self.text_placeholder = self.config.get("text_placeholder", "<FEEDBACK_TEXT>")
        self.default_labels = self.config.get(
            "default_labels", {"severity": "low", "urgency": "low", "impact": "low"}
        )

        # Initialize LLM oracle
        self.oracle = LLMOracle(model_name=model_name)

    def _build_prompt(self, feedback_text: str) -> str:
        """
        Construct the prompt by combining instructions, definitions, example, and feedback.
        """
        # YAML sections
        definitions = self.config.get("definitions", {})
        instructions = self.config.get("instructions", "")
        example = self.config.get("example", {})

        # Convert definitions to text block
        definitions_text = "Definitions:\n"
        for key, value in definitions.items():
            definitions_text += f"- {key}:\n"
            for lvl, desc in value.items():
                definitions_text += f"    {lvl}: {desc}\n"

        # Example output block
        example_text = ""
        if example:
            ex_feedback = example.get("feedback", "")
            ex_output = example.get("output", "")
            example_text = f"Example feedback:\n{ex_feedback}\nExpected JSON output:\n{ex_output}\n"

        # Final prompt with feedback inserted
        prompt = (
            f"{instructions}\n\n"
            f"{definitions_text}\n\n"
            f"{example_text}\n"
            f"Label this feedback strictly in JSON:\n{feedback_text}"
        )
        return prompt

    def label_and_save(
        self,
        df: pd.DataFrame,
        output_path: str,
        label_cols: list = ["severity", "urgency", "impact"]
    ):
        """
        Labels the given DataFrame using the LLM and saves the updated CSV/TSV.
        """
        n_rows = len(df)
        logger.info(f"Labeling {n_rows} rows...")

        # Prepare label columns in DataFrame
        for col in label_cols:
            if col not in df.columns:
                df[col] = None

        # Label each row
        for idx, row in df.iterrows():
            feedback_text = row["feedback_text"]
            prompt = self._build_prompt(feedback_text)

            parsed = None
            last_error = None

            for attempt in range(MAX_RETRIES):
                try:
                    raw_output = self.oracle.label(prompt).strip()

                    if raw_output.startswith("```"):
                        raw_output = raw_output.strip("`").replace("json", "").strip()

                    parsed = self.oracle.parse_to_proposal(raw_output)
                    break  # success

                except Exception as e:
                    last_error = e
                    logger.warning(
                        f"Parse failed (row {idx}, attempt {attempt + 1}): {e}"
                    )

                    # Tighten the prompt for retry
                    prompt = (
                        "Your previous response was invalid JSON.\n"
                        "Return ONLY a valid JSON object with exactly these keys:\n"
                        'severity, urgency, impact.\n'
                        "No explanations. No markdown. No extra text.\n\n"
                        f"Feedback:\n{feedback_text}"
                    )

            if parsed is None:
                logger.warning(
                    f"Falling back to defaults for row {idx}: {last_error}"
                )
                parsed = self.default_labels

            for col in label_cols:
                df.at[idx, col] = parsed.get(col, self.default_labels[col])

        # Save labeled dataset
        df.to_csv(output_path, sep="\t", index=False)
        logger.info(f"Saved labeled dataset to {output_path}")
